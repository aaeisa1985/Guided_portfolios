from decimal import Decimal
from collections import defaultdict
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import LedgerEntry, LedgerJournal, ExecutionFill, InvestmentOrder, PortfolioPosition, ValuationSnapshot

CENT=Decimal("0.01")
def money(v): return Decimal(v).quantize(CENT)

def reconcile_account(session:Session, account_id):
    journals=session.scalars(select(LedgerJournal).where(LedgerJournal.account_id==account_id)).all()
    journal_results=[]
    for journal in journals:
        rows=session.scalars(select(LedgerEntry).where(LedgerEntry.journal_id==journal.id)).all()
        debit=sum((r.amount for r in rows if r.direction=="DEBIT"),Decimal("0"))
        credit=sum((r.amount for r in rows if r.direction=="CREDIT"),Decimal("0"))
        journal_results.append({"journalId":journal.id,"balanced":money(debit)==money(credit),"debit":money(debit),"credit":money(credit)})
    fills=session.execute(select(ExecutionFill,InvestmentOrder).join(InvestmentOrder,InvestmentOrder.id==ExecutionFill.order_id).where(InvestmentOrder.account_id==account_id)).all()
    expected=defaultdict(lambda:Decimal("0"))
    for fill,order in fills:
        key=(order.portfolio_id,order.instrument_id)
        expected[key] += fill.quantity if order.side=="BUY" else -fill.quantity
    positions=session.scalars(select(PortfolioPosition).where(PortfolioPosition.account_id==account_id)).all()
    actual={(p.portfolio_id,p.instrument_id):p.quantity for p in positions}
    position_mismatches=[]
    for key in sorted(set(expected)|set(actual),key=str):
        exp=money(expected.get(key,0)); act=money(actual.get(key,0))
        if exp!=act: position_mismatches.append({"portfolioId":key[0],"instrumentId":key[1],"expected":exp,"actual":act})
    journalized=session.scalars(select(LedgerEntry).where(LedgerEntry.account_id==account_id,LedgerEntry.journal_id.is_not(None))).all()
    debit=sum((e.amount for e in journalized if e.direction=="DEBIT"),Decimal("0"))
    credit=sum((e.amount for e in journalized if e.direction=="CREDIT"),Decimal("0"))
    double_entry_ok=money(debit)==money(credit)
    latest=sess=snapshot=session.scalar(select(ValuationSnapshot).where(ValuationSnapshot.account_id==account_id).order_by(ValuationSnapshot.as_of.desc()))
    valuation_ok=None
    if snapshot:
        current_market=sum((p.quantity*p.market_price for p in positions if p.quantity>0),Decimal("0"))
        cash_rows=[e for e in journalized if e.ledger_account=="CASH"]
        current_cash=sum((e.amount if e.direction=="DEBIT" else -e.amount for e in cash_rows),Decimal("0"))
        valuation_ok=money(current_market+current_cash)==money(snapshot.nav)
    return {
        "accountId":account_id,
        "journalsBalanced":all(x["balanced"] for x in journal_results),
        "journalCount":len(journal_results),
        "doubleEntryBalanced":double_entry_ok,
        "positionsMatchExecutions":not position_mismatches,
        "positionMismatches":position_mismatches,
        "valuationReconciled":valuation_ok,
        "overall":all([all(x["balanced"] for x in journal_results),double_entry_ok,not position_mismatches,valuation_ok is not False])
    }
