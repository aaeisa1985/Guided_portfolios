from datetime import datetime,timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models import Base,Customer,InvestmentAccount,Portfolio,Instrument,PortfolioPosition,CorporateAction
from app.services.corporate_actions import process_corporate_action,approve_corporate_action
def test_split_maker_checker():
    engine=create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
    with Session(engine) as s:
        maker=Customer(customer_id="M",full_name="Maker",email="m@example.com",password_hash="x",role="MANAGER")
        checker=Customer(customer_id="C",full_name="Checker",email="c@example.com",password_hash="x",role="MANAGER")
        account=InvestmentAccount(customer_id=maker.id,account_number="A"); portfolio=Portfolio(name="P",slug="p",category="TEST",objective="Test",risk_level=3); inst=Instrument(symbol="TST",name="Test",instrument_type="STOCK",asset_class="EQUITY")
        s.add_all([maker,checker,account,portfolio,inst]); s.flush()
        pos=PortfolioPosition(account_id=account.id,portfolio_id=portfolio.id,instrument_id=inst.id,quantity=100,average_cost=40,market_price=50,currency="AED")
        ca=CorporateAction(instrument_id=inst.id,action_type="SPLIT",ex_date=datetime.now(timezone.utc),effective_date=datetime.now(timezone.utc),ratio_numerator=2,ratio_denominator=1,created_by=maker.id)
        s.add_all([pos,ca]); s.flush(); approve_corporate_action(s,ca,checker); process_corporate_action(s,ca); s.commit()
        assert pos.quantity==200 and pos.average_cost==20 and ca.status=="COMPLETED"
