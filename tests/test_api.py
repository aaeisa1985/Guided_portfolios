import os
os.environ["XCOMPANY_JWT_SECRET"]="test-secret-for-suite"
os.environ["DATABASE_URL"]="sqlite:///./data/test_xcompany.db"

from fastapi.testclient import TestClient
from app.main import app, Base, engine

Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
client=TestClient(app)

def test_health_and_readiness():
    assert client.get("/health").status_code==200
    assert client.get("/health/ready").json()["status"]=="ready"

def test_register_and_me():
    r=client.post("/api/v1/auth/register",json={"full_name":"Test Investor","email":"test@example.com","password":"Password123!"})
    assert r.status_code==200
    token=r.json()["access_token"]
    me=client.get("/api/v1/auth/me",headers={"Authorization":f"Bearer {token}"})
    assert me.status_code==200
    assert me.json()["customerId"].startswith("C-")

def test_protected_route_requires_auth():
    assert client.get("/api/v1/positions").status_code==401


def test_execution_updates_position_and_balances_ledger():
    from decimal import Decimal
    from sqlalchemy.orm import Session
    from app.models import Customer,InvestmentAccount,Portfolio,Instrument,InvestmentOrder,LedgerEntry,PortfolioPosition
    from app.services.execution import apply_execution,assert_journal_balanced
    with Session(engine) as s:
        customer=Customer(customer_id="C-EXEC-1",full_name="Execution Test",email="exec@example.com",password_hash="x")
        s.add(customer); s.flush()
        account=InvestmentAccount(customer_id=customer.id,account_number="ACC-EXEC-1"); portfolio=Portfolio(name="Test",slug="test-exec",category="TEST",objective="Test",risk_level=2)
        instrument=Instrument(symbol="TST",name="Test Instrument",instrument_type="ETF",asset_class="EQUITY")
        s.add_all([account,portfolio,instrument]); s.flush()
        order=InvestmentOrder(account_id=account.id,portfolio_id=portfolio.id,instrument_id=instrument.id,side="BUY",order_type="MARKET",quantity=Decimal("10"))
        s.add(order); s.flush()
        fill=apply_execution(s,order,"EXEC-1",Decimal("10"),Decimal("100"),Decimal("2"))
        s.flush()
        assert fill.quantity==Decimal("10")
        pos=s.query(PortfolioPosition).one()
        assert pos.quantity==Decimal("10")
        assert pos.average_cost==Decimal("100.20")
        journal_id=s.query(LedgerEntry.journal_id).first()[0]
        assert assert_journal_balanced(s,journal_id)
        s.commit()


def test_execution_partial_fill_idempotency_and_oversell():
    from decimal import Decimal
    from sqlalchemy.orm import Session
    from app.models import InvestmentOrder,ExecutionFill,PortfolioPosition
    from app.services.execution import apply_execution
    with Session(engine) as s:
        position=s.query(PortfolioPosition).first()
        order=InvestmentOrder(account_id=position.account_id,portfolio_id=position.portfolio_id,instrument_id=position.instrument_id,side="BUY",order_type="MARKET",quantity=Decimal("10"))
        s.add(order); s.flush()
        first=apply_execution(s,order,"EXEC-PART-1",Decimal("4"),Decimal("100"))
        assert order.status=="PARTIALLY_FILLED"
        second=apply_execution(s,order,"EXEC-PART-2",Decimal("6"),Decimal("110"))
        assert order.status=="FILLED"
        assert s.query(ExecutionFill).filter_by(order_id=order.id).count()==2
        replay=apply_execution(s,order,"EXEC-PART-2",Decimal("6"),Decimal("999"))
        assert replay.id==second.id
        assert position.quantity==Decimal("20")
        sell=InvestmentOrder(account_id=position.account_id,portfolio_id=position.portfolio_id,instrument_id=position.instrument_id,side="SELL",order_type="MARKET",quantity=Decimal("999"))
        s.add(sell); s.flush()
        try:
            apply_execution(s,sell,"EXEC-OVERSELL-2",Decimal("999"),Decimal("100"))
            assert False, "oversell must be rejected"
        except ValueError as exc:
            assert "available position" in str(exc)
        s.rollback()
