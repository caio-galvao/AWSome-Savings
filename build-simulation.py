import csv
import pandas as pd
from aws_model import optimize_model

# This file generates the input for aws_model and generates the output in a better format.

# It receives 3 csv files:
# - input: values for every market for every instance used in the simulation
# - input_sp: values for savings plan for every instance used in the simulation
# - TOTAL_demand: demand for all instances (including instances not used in the simulation)
# There are examples of thoses files in the data folder.

# It generates the following csv files:
# - resultCost: the total cost of the simulation, the cost for every instance and the total savings plan cost
# - total_purchases_savings_plan: for every hour, the active value and the value reserved for savings plan
# - total_purchases_{instance_name}: one file for every instance. It has, for every hour and every market 
# type (including savings plan), the number of active instances and the number of reserves made.

def checkInputSP(sp_input, instances): #TO DO
    #if sp_input['instance'].value_counts() != instances: return False
    #if len(sp_input['y'].value_counts()) != 1: return False

    return True

# Generates total_purchases for every instance and the instance values in resultCost
def outputInstances(values, t, instance_names, market_names, input_data, writerCost): #is it possible to calcule the savings plan cost of each instance?

    for i_instance in range(len(instance_names)):
        cost = 0

        output = open('total_purchases_' + instance_names[i_instance] + '.csv', 'w')
        writer = csv.writer(output)
        writer.writerow(['instanceType', 'market', 'count_active', 'count_reserves'])

        #Savings plan
        for i_time in range(t):
            active = values[i_time][i_instance + 1][0][0]
            writer.writerow([instance_names[i_instance], 'savings_plan', active, 0])

            #the individual instance cost in the output does not considers savings plan cost
                
        #Other markets
        for i_market in range(len(market_names)):
            im_values = input_data[i_instance][i_market]
            cr_im = im_values[0] * im_values[2] + im_values[1]

            for i_time in range(t):
                active = values[i_time][i_instance + 1][i_market + 1][0]
                reserves = values[i_time][i_instance + 1][i_market + 1][1]
                writer.writerow([instance_names[i_instance], market_names[i_market], active, reserves])

                cost += reserves * cr_im

        writerCost.writerow([instance_names[i_instance], cost])        
        output.close()

# Generates total_purchases_savings_plan and the savings plan value in resultCost
def outputSavingsPlan(values, t, y_sp, writerCost):
    output = open('total_purchases_savings_plan.csv', 'w')
    writer = csv.writer(output)
    writer.writerow(['market', 'value_active', 'value_reserves'])
    cost = 0

    for i_time in range(t):
        values_sp = values[i_time][0][0]
        cost += values_sp[1] * y_sp
        writer.writerow(['savings_plan', values_sp[0], values_sp[1]])

    writerCost.writerow(['savings_plan', cost])


def generate_list(values, t, num_instances, num_markets):
    index = 0
    list = []
    for i_time in range(t):
        list_time = []
        list_time.append([[values[index], values[index + 1]]])
        index += 2
        for i_instance in range(num_instances):
            list_instance = []
            list_instance.append([values[index]])
            index += 1
            for i_market in range(num_markets):
                list_instance.append([values[index], values[index + 1]])
                index += 2
            list_time.append(list_instance)
        list.append(list_time)
    return list

raw_input = pd.read_csv('data/input.csv')
raw_sp_input = pd.read_csv('data/input_sp.csv')
instances = raw_input['instance'].value_counts()

if checkInputSP(raw_sp_input, instances) == False:
    raise ValueError("Error in the savings plan input.")

raw_demand = pd.read_csv('data/TOTAL_demand.csv')

resultCost = open('data/resultCost.csv', 'w')
writerCost = csv.writer(resultCost)
writerCost.writerow(['instance','total_cost'])

input_data = []
input_sp = []
total_demand = []
instance_names = []

for instance in instances.index:
    line_sp = raw_sp_input[raw_sp_input['instance'] == instance]
    input_sp.append(line_sp['p_hr'])
    instance_input = []
    market_names = []
    instance_names.append(instance)

    for i in range(len(raw_input)):
        line = raw_input.iloc[i]
        if line['instance'] == instance:
            instance_input.append([line['p_hr'],line['p_up'], line['y']])
            market_names.append(line['market_name'])
    input_data.append(instance_input)

    instance_demand = raw_demand[instance].values.tolist()
    total_demand.append(instance_demand)

t = len(total_demand[0])
y_sp = (raw_sp_input.iloc[0])['y']

result = optimize_model(t, total_demand, input_data, input_sp, y_sp)
cost = result[0]
values = generate_list(result[1], t, len(instance_names), len(market_names))

writerCost.writerow(['all', cost])

outputSavingsPlan(values, t, y_sp, writerCost)
outputInstances(values, t, instance_names, market_names, input_data, writerCost)