from modelx.serialize.jsonvalues import *

_formula = None

_bases = [
    ".Cashflows"
]

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def CF_Net_BOP(t):
    pol_term = Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return (  CF_Comm(t)
                + CF_Init_Exp(t)
                + CF_Ren_Exp(t)
                - CF_Premiums(t))


def CF_Inv_Income(t):
    pol_term = Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return CF_Net_BOP(t) * Get_Interest_Rate(t)


def Reserve_IF(t):
    pol_term = Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        net_cf = (  CF_Net_BOP(t+1)
                  + CF_Inv_Income(t+1)
                  + CF_Death_Ben(t+1))
        return (net_cf + Reserve_IF(t+1)) / (1 + Get_Interest_Rate(t+1))


def Reserve_PP(t):
    pol_term = Get_Data_Value("policy_term")

    if t <= 0 or t > pol_term * 12:
        return 0
    else:
        return Reserve_IF(t) / Prob_IF_E(t)


# ---------------------------------------------------------------------------
# References

Basis = "RES"