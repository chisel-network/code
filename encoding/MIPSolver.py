
class MIPSolver:

    def Variable(self, type):
        return None

    def Assert(self, constraint):
        pass

    def Maximize(self, objective):
        pass

    def Solve(self):
        pass

    def Value(self, variable):
        return None
    
import gurobipy
from gurobipy import GRB

class GurobiSolver(MIPSolver):
    def __init__(self):
        self.constraints = []
        self.objective = None
        self.problem = gurobipy.Model("mip")

    def Variable(self, type = None, name=None):
        if type == "Int":
            var = self.problem.addVar(vtype=GRB.INTEGER, name=name)
        if type == "Bool":
            var = self.problem.addVar(vtype=GRB.BINARY, name=name)
        else:
            var = self.problem.addVar(name=name)
        # self.problem.update()
        return var
    
    def Variables(self, dim1, dim2, type = None, name=None):
        if type == "Int":
            var = self.problem.addVars(dim1, dim2, vtype=GRB.INTEGER, name=name)
        if type == "Bool":
            var = self.problem.addVars(dim1, dim2, vtype=GRB.BINARY, name=name)
        else:
            var = self.problem.addVars(dim1, dim2, name=name)
            
        # self.problem.update()
        return var
    
    def FixedVariable(self, type, name=None, value=None):
        var = self.problem.addVar(vtype=GRB.BINARY, ub=value, lb=value, name=name)
        return var
    
    def Maximize(self, objective):
        self.problem.setObjective(objective, GRB.MAXIMIZE)
        self.objective = objective
        # self.problem.update()
        
    def Minimize(self, objective):
        self.problem.setObjective(objective, GRB.MINIMIZE)
        self.objective = objective
        # self.problem.update()

    def Assert(self, constraint, name=""):
        self.constraints.append(constraint)
        self.problem.addConstr(constraint, name=name)
        # self.problem.update()
        
    def Solve(self):
        assert self.objective
        # self.problem.update()
        self.problem.optimize()

    def Value(self, var):
        return var.x
    
    def AssertIndiatorConstraint(self, lhs, rhs):
        self.constraints.append(lhs >> rhs)
        self.problem.addConstr(lhs >> rhs)
        # self.problem.update()

    def __repr__(self):
        return ""
