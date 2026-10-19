def rank_actions(actions, shortage_amount):
    if float(shortage_amount)<0: raise ValueError("shortage_amount must be non-negative")
    required={"name","estimated_cash_relief","estimated_cost","feasible","evidence","uncertainty"}; out=[]
    for a in actions:
        if not required.issubset(a): raise ValueError(f"Action missing keys: {sorted(required-set(a))}")
        relief=float(a["estimated_cash_relief"]); cost=float(a["estimated_cost"])
        if relief<0 or cost<0: raise ValueError("Relief and cost must be non-negative")
        out.append({**a,"net_estimated_benefit":relief-cost,"covers_shortfall":relief>=shortage_amount,"rank_score":relief-cost if a["feasible"] else float("-inf")})
    return sorted(out,key=lambda a:a["rank_score"],reverse=True)
