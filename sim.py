from __future__ import annotations
from datetime import datetime
import os 
if len(__name__.split("."))==1:
	from calc import *
else:
	from .calc import *
from typing import *
from dataclasses import dataclass
TOLERATED_ERROR = 1e-8
from ctypes import *
libsim = CDLL(os.path.dirname(os.path.realpath(__file__)) + "/cmodules/libsim.so")
from math import ceil

class SimParams():
	#when implemented, the batteries will come after the flexibility, or both will be used by python's optimize
	#defaults to false
	has_solar             : bool
	has_wind              : bool
	has_bioenergy         : bool
	has_piloted_bioenergy : bool
	has_battery           : bool
	has_flexibility       : bool

	#defaults to true
	has_solar_scaling             : bool
	has_wind_scaling              : bool
	has_bioenergy_scaling         : bool
	has_piloted_bioenergy_scaling : bool
	has_consumer_scaling          : Union[bool, List[bool]]

	#defaults to 0.0
	solar_power             : float
	wind_power              : float
	bioenergy_power         : float
	battery_capacity        : float
	piloted_bioenergy_power : float
	flexibility_ratio       : Union[float, List[float]]
	consumer_power          : Union[float, List[float]]
	consumer_contrib        : List[float]
	#defaults to None
	solar_curve             : PowerData
	wind_curve              : PowerData
	bioenergy_curve         : PowerData
	consumer_curves         : Union[List[PowerData], PowerData]

	#date params, defaults to None
	begin                   : datetime
	end                     : datetime
	def __init__(self, \
		has_solar                     : bool = False,\
		has_wind                      : bool = False,\
		has_bioenergy                 : bool = False,\
		has_piloted_bioenergy         : bool = False,\
		has_battery                   : bool = False,\
		has_flexibility               : bool = False,\
		has_solar_scaling             : bool = True,\
		has_wind_scaling              : bool = True,\
		has_bioenergy_scaling         : bool = True,\
		has_piloted_bioenergy_scaling : bool = True,\
		has_consumer_scaling          : Union[bool, List[bool]] = False,\
		solar_power                   : float = 0.0,\
		wind_power                    : float = 0.0,\
		bioenergy_power               : float = 0.0,\
		battery_capacity              : float = 0.0,\
		piloted_bioenergy_power       : float = 0.0,\
		flexibility_ratio             : Union[float, List[float]] = 0.0,\
		consumer_power                : Union[float, List[float]] = 0.0,\
		consumer_contrib              : List[float] = None,\
		solar_curve                   : PowerData = None,\
		wind_curve                    : PowerData = None,\
		bioenergy_curve               : PowerData = None,\
		consumer_curves               : Union[List[PowerData], PowerData] = None,\
		begin                         : datetime = None,\
		end                           : datetime = None
	) -> None:
		self.has_solar             : bool = has_solar
		self.has_wind              : bool = has_wind
		self.has_bioenergy         : bool = has_bioenergy
		self.has_piloted_bioenergy : bool = has_piloted_bioenergy
		self.has_battery           : bool = has_battery
		self.has_flexibility       : bool = has_flexibility
		
		self.has_solar_scaling             : bool = has_solar_scaling
		self.has_wind_scaling              : bool = has_wind_scaling
		self.has_bioenergy_scaling         : bool = has_bioenergy_scaling
		self.has_piloted_bioenergy_scaling : bool = has_piloted_bioenergy_scaling
		self.has_consumer_scaling          : Union[bool, List[bool]] = has_consumer_scaling

		self.solar_power             : float = solar_power
		self.wind_power              : float = wind_power
		self.bioenergy_power         : float = bioenergy_power
		self.battery_capacity        : float = battery_capacity
		self.piloted_bioenergy_power : float = piloted_bioenergy_power
		self.flexibility_ratio       : Union[float, List[float]] = flexibility_ratio
		self.consumer_power          : Union[float, List[float]] = consumer_power
		self.consumer_contrib        : Union[float, List[float]] = consumer_contrib

		self.solar_curve             : PowerData = solar_curve.get_copy() 
		self.wind_curve              : PowerData = wind_curve.get_copy()
		self.bioenergy_curve         : PowerData = bioenergy_curve.get_copy()
		self.consumer_curves         : Union[PowerData, List[PowerData]] = consumer_curves if isinstance(consumer_curves, PowerData) else [c.get_copy() for c in consumer_curves]

		self.begin                   : datetime = begin
		self.end                     : datetime = end

		self.check_and_convert_params()

	def get_clone(self) -> SimParams:
		return SimParams(
			has_solar                     = self.has_solar                    ,
			has_wind                      = self.has_wind                     ,
			has_bioenergy                 = self.has_bioenergy                ,
			has_piloted_bioenergy         = self.has_piloted_bioenergy        ,
			has_battery                   = self.has_battery                  ,
			has_flexibility               = self.has_flexibility              ,
			has_solar_scaling             = self.has_solar_scaling, 
			has_wind_scaling              = self.has_bioenergy_scaling        , 
			has_bioenergy_scaling         = self.has_wind_scaling             , 
			has_piloted_bioenergy_scaling = self.has_piloted_bioenergy_scaling, 
			has_consumer_scaling          = self.has_consumer_scaling if isinstance(self.has_consumer_scaling, bool) else self.has_consumer_scaling[:],
			solar_power                   = self.solar_power                  ,
			wind_power                    = self.wind_power                   ,
			bioenergy_power               = self.bioenergy_power              ,
			battery_capacity              = self.battery_capacity             ,
			piloted_bioenergy_power       = self.piloted_bioenergy_power      ,
			flexibility_ratio             = self.flexibility_ratio if isinstance(self.flexibility_ratio, float) else self.flexibility_ratio[:],
			consumer_power                = self.consumer_power    if isinstance(self.consumer_power   , float) else self.consumer_power   [:], 
			consumer_contrib              = self.consumer_contrib[:]          ,
			solar_curve                   = self.solar_curve    .get_copy()  ,
			wind_curve                    = self.wind_curve     .get_copy()  ,
			bioenergy_curve               = self.bioenergy_curve.get_copy()  ,
			consumer_curves               = self.consumer_curves if isinstance(self.consumer_curves, PowerData) else [c.get_copy() for c in self.consumer_curves]
		)
	def get_copy(self) -> SimParams:
		return self.get_clone()
	def get_wind_curve(self) -> PowerData:
		if (not self.has_wind):
			raise Exception("no wind curve in this config")
		if (self.has_wind_scaling):
			return self.wind_curve.get_slice_over_period(self.begin, self.end).get_scaled(self.wind_power)
		return self.wind_curve.get_slice_over_period(self.begin, self.end)

	def get_solar_curve(self) -> PowerData:
		if (not self.has_solar):
			raise Exception("no solar curve in this config")
		if (self.has_solar_scaling):
			return self.solar_curve.get_slice_over_period(self.begin, self.end).get_scaled(self.solar_power)
		return self.solar_curve.get_slice_over_period(self.begin, self.end)

	def get_constant_bioenergy_curve(self) -> PowerData:
		if (not self.has_bioenergy):
			raise Exception("no non-piloted bioenergy curve in this config")
		if (self.has_bioenergy_scaling):
			return self.bioenergy_curve.get_slice_over_period(self.begin, self.end).get_scaled(self.bioenergy_power)
		return self.bioenergy_curve.get_slice_over_period(self.begin, self.end)
	
	def get_consumers_agglomerated_curves(self) -> PowerData:
		#usefull when there is no flexibility
		toReturn : PowerData = None
		for i in range(len(self.consumer_curves)):
			curve = self.consumer_curves[i].get_slice_over_period(self.begin, self.end)
			if toReturn is not None:
				#this may be slow, a has_same_dates will later be added to powerdata
				intersec = curve.get_intersect(toReturn)
				curve = curve.get_slice(intersec)
				toReturn = toReturn.get_slice(toReturn)
			if (self.has_consumer_scaling[i]):
				curve = curve.get_scaled(self.consumer_power[i])
			curve *= self.consumer_contrib[i]
			if toReturn is None:
				toReturn = curve
			else:
				toReturn += curve
		return toReturn
	def get_consumers_curve_index(self, index : int = 0) -> PowerData:
		if index >= len(self.consumer_curves) or index < 0:
			raise Exception("index out of range")
		curve = self.consumer_curves[index].get_slice_over_period(self.begin, self.end)
		if self.has_consumer_scaling[index] is True:
			curve = curve.get_scaled(self.consumer_power[index])
		curve *= self.consumer_contrib[index]
	def check_and_convert_params(self):
		if self.has_solar and self.solar_curve == None:
			raise Exception("solar production curve needed but not initialized")
		if self.has_wind and self.wind_curve == None:
			raise Exception("wind turbine production curve needed but not initialized")
		if self.has_bioenergy and self.bioenergy_curve == None:
			raise Exception("non pilotable bioenergy curve needed but not initialized")
		if self.consumer_curves is None:
			raise Exception("consumer curves are mandatory")

		if isinstance(self.consumer_curves, PowerData):
			self.consumer_curves = [self.consumer_curves]
		if isinstance(self.has_consumer_scaling, bool):
			self.has_consumer_scaling = [self.has_consumer_scaling] * len(self.consumer_curves)
		if isinstance(self.consumer_power, float):
			self.consumer_power = [self.consumer_power] * len(self.consumer_curves)
		if self.has_flexibility is True and isinstance(self.flexibility_ratio, float):
			self.flexibility_ratio = [self.flexibility_ratio] * len(self.consumer_curves)
		if self.consumer_contrib is None:
			self.consumer_contrib = [1.0/len(self.consumer_curves)] * len(self.consumer_curves)
		
		if len(self.consumer_curves) != len(self.has_consumer_scaling):
			raise Exception("consumer curves and their scaling MUST be the same length")
		if len(self.consumer_curves) != len(self.consumer_power):
			raise Exception("consumer curves and their power MUST be the same length")
		if len(self.consumer_curves) != len(self.consumer_contrib):
			raise Exception("consumer curves and their contributions MUST be the same length")
		if self.has_flexibility is True and len(self.consumer_curves) != len(self.flexibility_ratio):
			raise Exception("consumer curves and their flexibility ratio MUST be the same length")
		#gets all the curves to the sames date places
		curves_to_intersect = self.consumer_curves[:]
		if (self.has_solar):
			curves_to_intersect.append(self.solar_curve)
		if (self.has_bioenergy):
			curves_to_intersect.append(self.bioenergy_curve)
		if (self.has_wind):
			curves_to_intersect.append(self.wind_curve)
		intersect = curves_to_intersect[0].get_multiple_intersect(curves_to_intersect)
		for i in range(len(self.consumer_curves)):
			self.consumer_curves[i] = self.consumer_curves[i].get_slice(intersect)
		if (self.has_solar):
			self.solar_curve = self.solar_curve.get_slice(intersect)
		if (self.has_bioenergy):
			self.bioenergy_curve = self.bioenergy_curve.get_slice(intersect)
		if (self.has_wind):
			self.wind_curve = self.wind_curve.get_slice(intersect)
		
@dataclass(init=True)
class SimResults():
	total_consumption           : PowerData
	production_before_batteries : PowerData
	total_production            : PowerData
	imported_power              : PowerData
	exported_power              : PowerData
	battery                     : Battery
	flexibility_usage           : PowerData
	def get_slice_over_period(self, begin : datetime, end : datetime) -> SimResults:
		return SimResults(
			total_consumption           = self.total_consumption          .get_slice_over_period(begin, end) if (self.total_consumption           != None) else None,
			production_before_batteries = self.production_before_batteries.get_slice_over_period(begin, end) if (self.production_before_batteries != None) else None, 
			total_production            = self.total_production           .get_slice_over_period(begin, end) if (self.total_production            != None) else None, 
			imported_power              = self.imported_power             .get_slice_over_period(begin, end) if (self.imported_power              != None) else None, 
			exported_power              = self.exported_power             .get_slice_over_period(begin, end) if (self.exported_power              != None) else None, 
			battery                     = self.battery                    .get_slice_over_period(begin, end) if (self.battery                     != None) else None, 
			flexibility_usage           = self.flexibility_usage          .get_slice_over_period(begin, end) if (self.flexibility_usage           != None) else None, 
			)
	def get_rolling_average(self, width : int) -> SimResults:
		return SimResults(
			total_consumption           = self.total_consumption          .get_rolling_average(width) if (self.total_consumption           != None) else None,
			production_before_batteries = self.production_before_batteries.get_rolling_average(width) if (self.production_before_batteries != None) else None,
			total_production            = self.total_production           .get_rolling_average(width) if (self.total_production            != None) else None,
			imported_power              = self.imported_power             .get_rolling_average(width) if (self.imported_power              != None) else None,
			exported_power              = self.exported_power             .get_rolling_average(width) if (self.exported_power              != None) else None,
			battery                     = self.battery                    .get_rolling_average(width) if (self.battery                     != None) else None,
			flexibility_usage           = self.flexibility_usage          .get_rolling_average(width) if (self.flexibility_usage           != None) else None,
			)

def simulate_flexibility(prod : PowerData, cons : PowerData, flex_ratio : float) -> Tuple[PowerData, PowerData]:
	day_indices = []
	last_date   = prod.dates[0]
	prod = prod.get_copy()
	cons = cons.get_copy()
	diff = cons - prod
	old_diff = diff.get_copy()
	for i in range(len(prod.dates)):
		#current idea : sort daily prod, cons and diff. Make an array with modif, and then process the data
		if ((prod.dates[i] - last_date).days >= 1):
			#time to sort data
			day_indices = sorted(day_indices, key=lambda x: diff.power[x])
			power_flex = 0
			for j in day_indices:
				power_flex += cons.power[j]
			power_flex = power_flex * flex_ratio
			power_down = power_flex
			power_up   = power_flex
			j = len(day_indices) - 1
			while (power_down > TOLERATED_ERROR):
				current_delta = power_down / len(day_indices)
				if (j > 0):
					current_delta = diff.power[day_indices[-1]] - diff.power[day_indices[j - 1]]
				nb_points = len(day_indices) - j
				power_to_substract = current_delta * nb_points
				power_to_substract = min(power_down, power_to_substract)
				if (power_to_substract != 0.0):
					for k in range(nb_points):
						cons.power[day_indices[k + j]] -= power_to_substract/nb_points
						power_down -= power_to_substract/nb_points
						diff.power[day_indices[k + j]] -= power_to_substract/nb_points
				j -= 1
				if (j < 0):
					j = 0
			j = 0
			while (power_up > TOLERATED_ERROR):
				current_delta = power_up / len(day_indices)
				if (j < len(day_indices) - 1):
					current_delta = diff.power[day_indices[j + 1]] - diff.power[day_indices[0]]
				nb_points = j + 1
				power_to_add = current_delta * nb_points
				power_to_add = min(power_up, power_to_add)
				if (power_to_add != 0.0):
					for k in range(nb_points):
						cons.power[day_indices[k]] += power_to_add/nb_points
						power_up -= power_to_add/nb_points
						diff.power[day_indices[k]] += power_to_add/nb_points
				j += 1
				if (j > len(day_indices) - 1):
					j = len(day_indices) - 1
			day_indices = []
			last_date = prod.dates[i]
		day_indices.append(i)
	return (prod,cons)

def simulate_flexibility_c(prod : PowerData, cons : PowerData, flex_ratio: float, deltatime : float):
	prod = prod.get_copy()
	cons = cons.get_copy()
	prod_timestamps = prod.get_dates_as_timestamps()
	flex_usage = np.array([0.0] * ceil((prod_timestamps[-1] - prod_timestamps[0]) / deltatime), dtype=np.float64)
	libsim.sim_flex(
	prod.power.ctypes.data_as(POINTER(c_double)),
	cons.power.ctypes.data_as(POINTER(c_double)),
	prod_timestamps.ctypes.data_as(POINTER(c_double)),
	len(prod.power),
	c_double(deltatime),
	c_double(flex_ratio),
	flex_usage.ctypes.data_as(POINTER(c_double))
	)
	return (prod, cons, PowerData([prod.dates[int(i * len(flex_usage)/len(prod.dates))] for i in range(len(flex_usage))] ,flex_usage))
	pass

def simulate_senario(params: SimParams) -> SimResults:
	total_consumption : PowerData = None #batteries are in reciever convention but are considered a "producer"
	battery : Battery = None
	total_consumption = params.get_consumers_agglomerated_curves()
	production : PowerData = None
	if params.has_wind:
		production = params.get_wind_curve() + production
	if params.has_solar:
		production = params.get_solar_curve() + production
	if params.has_bioenergy:
		production = params.get_constant_bioenergy_curve() + production
	production_before_flexibility = production.get_copy()
	diff_before_flexibility = (production - total_consumption)

	
	flex_usage = PowerData(params.bioenergy_curve.dates[:], np.array([1.0] * len(params.bioenergy_curve.dates[:])))
	if (params.has_flexibility):
		(production, total_consumption, flex_usage) = simulate_flexibility_c(production, total_consumption, params.flexibility_ratio[0], float(24*3600))
	production_before_batteries = production.get_copy()
	diff_before_batteries = (production - total_consumption)
	if params.has_battery:
		battery = Battery(params.battery_capacity)
		battery.from_power_data(diff_before_batteries)
		production = production - battery
	exported_power = (production - total_consumption).get_bigger_than(0.0)
	imported_power = (total_consumption - production).get_bigger_than(0.0)
	return SimResults(\
			total_consumption = total_consumption,\
			production_before_batteries = production_before_batteries,\
			total_production=production,\
			exported_power=exported_power,\
			imported_power=imported_power,\
			battery=battery,\
			flexibility_usage=flex_usage
		)
@dataclass(init=True)
class AgglomeratedSimResults:
	storage_use     : float 
	imported_power  : float 
	exported_power  : float 
	imported_time   : float 
	exported_time   : float 
	low_conso_peak  : float 
	high_conso_peak : float 
	low_import_peak : float 
	high_import_peak: float 
	flexibility_use : float 
	export_max      : float 
	import_max      : float 
	coverage        : float
	coverage_avg    : float
	autoconso       : float
	autoprod        : float
	@classmethod
	def from_sim_results (cls, result : SimResults) -> AgglomeratedSimResults:
		return AgglomeratedSimResults(
			storage_use     = (result.battery.get_bigger_than(0.0).get_average() / result.battery.capacity if result.battery.capacity != 0 else 1),
			imported_power  = result.imported_power.get_average(),
			exported_power  = result.exported_power.get_average(),
			imported_time   = (result.imported_power.count_greater_than(0.0) / len(result.imported_power.power)),
			exported_time   = (result.exported_power.count_greater_than(0.0) / len(result.exported_power.power)),
			low_conso_peak  = (result.total_consumption.get_percentile(5)),
			high_conso_peak = (result.total_consumption.get_percentile(95)),
			low_import_peak = (result.imported_power.get_percentile(5)),
			high_import_peak= (result.imported_power.get_percentile(95)),
			flexibility_use = (result.flexibility_usage.get_average()),
			export_max      = (result.exported_power.power.max()),
			import_max      = (result.imported_power.power.max()),
			coverage        = (result.total_consumption.get_average() / result.total_production.get_average()),
			coverage_avg    = (result.total_consumption / result.total_production).get_average(),
			autoconso       = ((result.total_production - result.exported_power).get_average() / result.total_production.get_average()),
			autoprod        = ((result.total_consumption - result.imported_power).get_average() / result.total_consumption.get_average())
		)