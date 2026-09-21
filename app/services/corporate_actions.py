"""Idempotent corporate action processing with approval and reconciliation safeguards."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models import CorporateAction, CorporateActionEvent, PortfolioPosition, LedgerJournal, LedgerEntry, Instrument
QTY=Decimal("0.00000001"); MONEY=Decimal("0.01")
def q(v,quantum=QTY): return Decimal(v or 0).quantize(quantum,rounding=ROUND_HALF_UP)
def money(v): return q(v,MONEY)
def validate_action(ca):
    if ca.action_type in {"SPLIT","REVERSE_SPLIT","STOCK_DIVIDEND","RIGHTS_ISSUE"} and (not ca.ratio_numerator or not ca.ratio_denominator or ca.ratio_denominator<=0 or ca.ratio_numerator<=0): raise ValueError("A positive numerator/denominator ratio is required")
    if ca.action_type=="CASH_DIVIDEND" and (ca.dividend_per_share is None or ca.dividend_per_share<0): raise ValueError("Cash dividend requires a non-negative dividend_per_share")
    if ca.action_type=="RIGHTS_ISSUE" and (ca.subscription_price is None or ca.subscription_price<0): raise ValueError("Rights issue requires subscription_price")
    if ca.action_type=="MERGER" and (not ca.replacement_instrument_id or not ca.exchange_ratio or ca.exchange_ratio<=0): raise ValueError("Merger requires replacement instrument and positive exchange ratio")
def approve_corporate_action(session,ca,actor):
    if ca.status!="DRAFT": raise ValueError(f"Only DRAFT actions can be approved; current status={ca.status}")
    if ca.created_by==actor.id: raise ValueError("Maker/checker control: creator cannot approve the same action")
    validate_action(ca); ca.status="APPROVED"; ca.approved_by=actor.id; ca.approved_at=datetime.now(timezone.utc)
def _journal(session,pos,ca,description):
    j=LedgerJournal(account_id=pos.account_id,reference_type="CORPORATE_ACTION",reference_id=ca.id,currency=pos.currency,description=description); session.add(j); session.flush(); return j
def _entry(session,**kw): session.add(LedgerEntry(**kw))
def _event(session,ca,pos,j,qb,qa,pb,pa,ab,aa,cash=0,income=0,frac=0,cil=0):
    e=CorporateActionEvent(corporate_action_id=ca.id,position_id=pos.id,journal_id=j.id if j else None,quantity_before=qb,quantity_after=qa,price_before=pb,price_after=pa,average_cost_before=ab,average_cost_after=aa,cash_impact=money(cash),income_recognized=money(income),fractional_units=q(frac),cash_in_lieu=money(cil)); session.add(e); return e
def _positions(session,ca):
    return session.scalars(select(PortfolioPosition).where(PortfolioPosition.instrument_id==ca.instrument_id,PortfolioPosition.quantity>0).with_for_update()).all()
def _split(session,ca,reverse=False):
    ratio=q(ca.ratio_numerator/ca.ratio_denominator); ratio=1/ratio if reverse else ratio; events=[]
    for pos in _positions(session,ca):
        qb,pb,ab=pos.quantity,pos.market_price,pos.average_cost; qa=q(qb*ratio); pa=money(pb/ratio); aa=money(ab/ratio)
        pos.quantity,pos.market_price,pos.average_cost=qa,pa,aa; j=_journal(session,pos,ca,f"{ca.action_type} ratio={ratio}"); delta=qa-qb
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="CORPORATE_ACTION_MEMO",entry_type="CORPORATE_ACTION",direction="DEBIT",amount=0,currency=pos.currency,units=delta,description=f"{ca.action_type}: {qb} -> {qa}")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="CORPORATE_ACTION_MEMO",entry_type="CORPORATE_ACTION",direction="CREDIT",amount=0,currency=pos.currency,units=delta,description=f"{ca.action_type}: {qb} -> {qa}")
        events.append(_event(session,ca,pos,j,qb,qa,pb,pa,ab,aa))
    return events
def _cash_dividend(session,ca):
    events=[]
    for pos in _positions(session,ca):
        qb=pos.quantity; amount=money(qb*ca.dividend_per_share); j=_journal(session,pos,ca,f"CASH_DIVIDEND {ca.dividend_per_share} per share")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="CASH",entry_type="CORPORATE_ACTION",direction="DEBIT",amount=amount,currency=pos.currency,units=0,description="Cash dividend")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="DIVIDEND_INCOME",entry_type="CORPORATE_ACTION",direction="CREDIT",amount=amount,currency=pos.currency,units=0,description="Dividend income")
        events.append(_event(session,ca,pos,j,qb,qb,pos.market_price,pos.market_price,pos.average_cost,pos.average_cost,cash=amount,income=amount))
    return events
def _stock_dividend(session,ca):
    ratio=q(ca.ratio_numerator/ca.ratio_denominator); events=[]
    for pos in _positions(session,ca):
        qb,pb,ab=pos.quantity,pos.market_price,pos.average_cost; grant=q(qb*ratio); qa=qb+grant; aa=money((qb*ab)/qa) if qa else 0; value=money(grant*pb)
        pos.quantity,pos.average_cost=qa,aa; j=_journal(session,pos,ca,f"STOCK_DIVIDEND ratio={ratio}")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="INVESTMENT_ASSET",entry_type="CORPORATE_ACTION",direction="DEBIT",amount=value,currency=pos.currency,units=grant,description="Stock dividend entitlement")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="DIVIDEND_INCOME",entry_type="CORPORATE_ACTION",direction="CREDIT",amount=value,currency=pos.currency,units=0,description="Stock dividend income")
        events.append(_event(session,ca,pos,j,qb,qa,pb,pb,ab,aa,income=value))
    return events
def _rights(session,ca):
    ratio=q(ca.ratio_numerator/ca.ratio_denominator); events=[]
    for pos in _positions(session,ca):
        qb,pb,ab=pos.quantity,pos.market_price,pos.average_cost; rights=q(qb*ratio); j=_journal(session,pos,ca,f"RIGHTS_ISSUE entitlement={rights} subscription_price={ca.subscription_price}")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="RIGHTS_ENTITLEMENT_MEMO",entry_type="CORPORATE_ACTION",direction="DEBIT",amount=0,currency=pos.currency,units=rights,description="Rights entitlement; no cash movement until exercised")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="RIGHTS_ENTITLEMENT_MEMO",entry_type="CORPORATE_ACTION",direction="CREDIT",amount=0,currency=pos.currency,units=rights,description="Rights entitlement; no cash movement until exercised")
        events.append(_event(session,ca,pos,j,qb,qb,pb,pb,ab,ab))
    return events
def _merger(session,ca):
    new=session.get(Instrument,ca.replacement_instrument_id)
    if not new: raise ValueError("Replacement instrument not found")
    events=[]
    for pos in _positions(session,ca):
        qb,pb,ab=pos.quantity,pos.market_price,pos.average_cost; new_qty=q(qb*ca.exchange_ratio); new_basis=money(ab/ca.exchange_ratio)
        pos.quantity=0; pos.market_price=0; pos.average_cost=0
        new_pos=session.scalar(select(PortfolioPosition).where(PortfolioPosition.account_id==pos.account_id,PortfolioPosition.portfolio_id==pos.portfolio_id,PortfolioPosition.instrument_id==ca.replacement_instrument_id).with_for_update())
        if not new_pos:
            new_pos=PortfolioPosition(account_id=pos.account_id,portfolio_id=pos.portfolio_id,instrument_id=new.id,currency=new.currency,quantity=0,average_cost=0,market_price=0,price_source="CORPORATE_ACTION"); session.add(new_pos); session.flush()
        old_qty,new_total=new_pos.quantity,new_pos.quantity+new_qty; new_pos.average_cost=money(((old_qty*new_pos.average_cost)+(new_qty*new_basis))/new_total) if new_total else 0; new_pos.quantity=new_total
        j=_journal(session,pos,ca,f"MERGER -> {new.id} exchange_ratio={ca.exchange_ratio}"); basis=money(qb*ab)
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="INVESTMENT_ASSET",entry_type="CORPORATE_ACTION",direction="CREDIT",amount=basis,currency=pos.currency,units=qb,description="Disposed legacy instrument")
        _entry(session,account_id=pos.account_id,journal_id=j.id,ledger_account="INVESTMENT_ASSET",entry_type="CORPORATE_ACTION",direction="DEBIT",amount=basis,currency=new.currency,units=new_qty,description="Received replacement instrument")
        events.append(_event(session,ca,pos,j,qb,0,pb,0,ab,0))
    return events
def process_corporate_action(session,ca):
    validate_action(ca)
    if ca.status=="COMPLETED": return session.scalars(select(CorporateActionEvent).where(CorporateActionEvent.corporate_action_id==ca.id)).all()
    if ca.status!="APPROVED": raise ValueError(f"Action must be APPROVED before execution; current status={ca.status}")
    existing=session.scalar(select(func.count()).select_from(CorporateActionEvent).where(CorporateActionEvent.corporate_action_id==ca.id))
    if existing: ca.status="COMPLETED"; return session.scalars(select(CorporateActionEvent).where(CorporateActionEvent.corporate_action_id==ca.id)).all()
    ca.status="PROCESSING"
    try:
        fn={"SPLIT":lambda:_split(session,ca),"REVERSE_SPLIT":lambda:_split(session,ca,True),"CASH_DIVIDEND":lambda:_cash_dividend(session,ca),"STOCK_DIVIDEND":lambda:_stock_dividend(session,ca),"RIGHTS_ISSUE":lambda:_rights(session,ca),"MERGER":lambda:_merger(session,ca)}[ca.action_type]
        events=fn(); ca.status="COMPLETED"; ca.executed_at=datetime.now(timezone.utc); ca.failure_reason=None; return events
    except Exception as exc:
        ca.status="FAILED"; ca.failure_reason=str(exc); raise
