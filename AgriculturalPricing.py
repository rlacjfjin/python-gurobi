import numpy as np
import pandas as pd
import gurobipy as grb

def data_prepare(dairy,components,qtyper,capacity,consumption,price,elasticity):
    qtyper_dict = dict()
    capacity_dict = dict()
    consumption_dict = dict()
    price_dict = dict()
    elasticity_dict = dict()
    k = 0
    for c in components:
        for d in dairy:
            i = (c,d)
            qtyper_dict[i] = qtyper[k]
            k = k+1
    k = 0
    for c in components:
        capacity_dict[c] = capacity[k]
        k = k+1
    k = 0
    for d in dairy:
        consumption_dict[d] = consumption[k]
        price_dict[d] = price[k]
        elasticity_dict[d] = elasticity[k]
        k = k+1
    return qtyper_dict,capacity_dict,consumption_dict,price_dict,elasticity_dict


def AgriculturalPricing(dairy,components,qtyper,capacity,consumption,price,elasticity,priceIndex,elasticity12,elasticity21):
    model = grb.Model('AgriculturalPricing')
    model.params.nonConvex = 2
    qvar = model.addVars(dairy, name="qvar")
    pvar = model.addVars(dairy, name="pvar")
    # Capacity
    model.addConstrs( (grb.quicksum(qtyper[c,d]*qvar[d] for d in dairy) <= capacity[c] for c in components  ),name='fatCap')
    # Price index
    model.addConstr( (grb.quicksum(consumption[d]*pvar[d] for d in dairy) <= priceIndex ), name='priceIndex')
    # Elasticity
    for d in dairy:
        if d in ['milk', 'butter']:
            model.addConstr( (qvar[d]-consumption[d])/consumption[d]
                                   == -elasticity[d]*(pvar[d]-price[d])/price[d], name='elas'+d)
        else:
            if d == "cheese1":
                d1 = "cheese2"
                e = elasticity12
            else:
                d1 = 'cheese1'
                e = elasticity21
            model.addConstr((qvar[d] - consumption[d]) / consumption[d]
                            == -elasticity[d] * (pvar[d] - price[d]) / price[d]
                            +  e * (pvar[d1] - price[d1]) / price[d1],
                            name='elas' + d)

    obj = grb.quicksum(qvar[d]*pvar[d] for d in dairy)
    model.setObjective(obj, grb.GRB.MAXIMIZE)
    model.optimize()
    price_demand = pd.DataFrame(columns=["Products", "Price", "Demand"])
    for d in dairy:
        price_demand = price_demand.append({"Products": d, "Price": '${:,.2f}'.format(round(1000*pvar[d].x)), "Demand": '{:,.2f}'.format(round(1e6*qvar[d].x))}, ignore_index=True)
    price_demand.index=[''] * len(price_demand)
    return price_demand

if __name__ == '__main__':
    dairy = ['milk', 'butter', 'cheese1', 'cheese2']
    components = ['fat', 'dryMatter']
    qtyper = [0.04,0.8,0.35,0.25,0.09,0.02,0.3,0.4]
    capacity = [600,750]
    consumption = [4.82,0.32,0.21,0.07]
    price = [0.297,0.72,1.05,0.815]
    elasticity = [0.4,2.7,1.1,0.4]
    priceIndex = 1.939
    elasticity12 = 0.1
    elasticity21 = 0.4
    qtyper_dict,capacity_dict,consumption_dict,price_dict,elasticity_dict = \
        data_prepare(dairy,components,qtyper,capacity,consumption,price,elasticity)
    price_demand = AgriculturalPricing(dairy,components,qtyper_dict,capacity_dict,consumption_dict,\
                                       price_dict,elasticity_dict,priceIndex,elasticity12,elasticity21)
    print(price_demand)