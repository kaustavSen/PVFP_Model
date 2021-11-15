from modelx.serialize.jsonvalues import *

_formula = None

_bases = []

_allow_none = None

_spaces = []

# ---------------------------------------------------------------------------
# Cells

def Get_Data_Value(Data_Var):
    return Policy_Data.query(f"policy_id == {MP_Num}").reset_index().at[0, Data_Var]


# ---------------------------------------------------------------------------
# References

MP_Num = 1

Policy_Data = ("DataClient", 139633484948912)