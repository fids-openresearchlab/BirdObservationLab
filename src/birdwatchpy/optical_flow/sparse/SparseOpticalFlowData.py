from copy import deepcopy
from dataclasses import dataclass


@dataclass
class SparseOpticalFlowData:
    x_old: float
    y_old: float
    x_new: float
    y_new: float
    distance: float

    def as_dict(self)  -> dict:
        sparse_opt_flow_data = deepcopy(self).__dict__
        sparse_opt_flow_data['distance']=float(sparse_opt_flow_data['distance'])
