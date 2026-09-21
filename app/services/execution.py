from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import InvestmentOrder,ExecutionFill,PortfolioPosition,LedgerJournal,LedgerEntry

CENT=Decimal("0.01")
def money(v): return Decimal(v).quantize(CENT,rounding=ROUND_HALF_UP)

def apply_execution(session:Session, order:InvestmentOrder, execution_id:str, quantity:Decimal, price:Decimal, fees:Decimal=Decimal("0"), executed_at=None):
    if quantity<=0 or price<=0 or fees<0: raise ValueError("Execution quantity and price must be positive; fees cannot be negative")
    existing=session.scalar(select(ExecutionFill).where(ExecutionFill.execution_id==execution_id))
    if existing: return existing
    fills=session.scalars(select(ExecutionFill).where(ExecutionFill.order_id==order.id)).all()
    executed=sum((f.quantity for f in fills),Decimal("0"))
    if executed+quantity>order.quantity: raise ValueError("Execution exceeds remaining order quantity")
    position=session.scalar(select(PortfolioPosition).where(
        PortfolioPosition.account_id==order.account_id,
        PortfolioPosition.portfolio_id==order.portfolio_id,
        PortfolioPosition.instrument_id==order.instrument_id
    ))
    if not position:
        position=PortfolioPosition(account_id=order.account_id,portfolio_id=order.portfolio_id,instrument_id=order.instrument_id,currency="AED")
        session.add(position); session.flush()
    notional=money(quantity*price)
    total=money(notional+fees)
    journal=LedgerJournal(account_id=order.account_id,reference_type="EXECUTION",reference_id=order.id,currency=position.currency,description=f"{order.side} execution {execution_id}")
    session.add(journal); session.flush()
    if order.side=="BUY":
        old_qty=position.quantity
        new_qty=old_qty+quantity
        position.average_cost=money(((old_qty*position.average_cost)+(quantity*price)+fees)/new_qty) if new_qty else Decimal("0")
        position.quantity=new_qty
        session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="INVESTMENT_ASSET",entry_type="EXECUTION",direction="DEBIT",amount=total,currency=position.currency,units=quantity,description="Asset acquired"))
        session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="CASH",entry_type="EXECUTION",direction="CREDIT",amount=total,currency=position.currency,units=0,description="Cash consideration and fees"))
    else:
        if quantity>position.quantity: raise ValueError("Sell execution exceeds available position")
        cost=money(quantity*position.average_cost)
        position.realized_pnl += money(notional-cost-fees)
        position.quantity -= quantity
        if position.quantity==0: position.average_cost=Decimal("0")
        session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="CASH",entry_type="EXECUTION",direction="DEBIT",amount=money(notional-fees),currency=position.currency,units=0,description="Cash proceeds net of fees"))
        session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="INVESTMENT_ASSET",entry_type="EXECUTION",direction="CREDIT",amount=cost,currency=position.currency,units=quantity,description="Asset disposed"))
        if fees:
            session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="FEES",entry_type="EXECUTION",direction="DEBIT",amount=fees,currency=position.currency,units=0,description="Execution fees"))
            session.add(LedgerEntry(account_id=order.account_id,journal_id=journal.id,ledger_account="CASH",entry_type="EXECUTION",direction="CREDIT",amount=fees,currency=position.currency,units=0,description="Execution fees"))
    fill=ExecutionFill(order_id=order.id,execution_id=execution_id,quantity=quantity,price=price,fees=fees,executed_at=executed_at or datetime.now(timezone.utc))
    session.add(fill)
    new_total=executed+quantity
    order.status="FILLED" if new_total==order.quantity else "PARTIALLY_FILLED"
    return fill

def assert_journal_balanced(session:Session,journal_id):
    rows=session.scalars(select(LedgerEntry).where(LedgerEntry.journal_id==journal_id)).all()
    debit=sum((r.amount for r in rows if r.direction=="DEBIT"),Decimal("0"))
    credit=sum((r.amount for r in rows if r.direction=="CREDIT"),Decimal("0"))
    if money(debit)!=money(credit): raise ValueError("Ledger journal is not balanced")
    return money(debit)==money(credit)
