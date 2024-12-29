import math
import numpy
import matplotlib.pyplot as pyplot
import heapq
import multiprocessing
import concurrent.futures

# m3tham ECE358 Lab 1 code, organized by question. Uncomment the question you would like to run the code for to simulate with correct parameters

T = 500
L = 2000
C = 1000000

def getExponentialRV(lmbda):
        U = numpy.random.uniform(0, 1)          # Uniform variable
        return -(1/lmbda) * math.log(1 - U)     # Formula in the lab manual to get exponential random variable

def q1():
    lmbda = 75  # Our lambda for this question
    n = 1000 
    # Generate 1000 exponential random variables
    exponentials = [getExponentialRV(lmbda) for _ in range(n)]

    # Calculate the mean and variance
    mean = numpy.mean(exponentials)
    var = numpy.var(exponentials)

    # Output the results
    print(f"Mean: {mean}")
    print(f"Variance: {var}")

def MM1(e):
    # Counters for number of arrivals, departures, observers, idle times, and total packets in the queue as observed at different observation events  
    Na = 0
    Nd = 0
    No = 0
    packets = 0
    idle = 0
    for event in e:
        if (event[1] == 'a'):           # Increment arrival counter if event is arrival
            Na += 1

        elif (event[1] == 'd'):         # Increment departure counter if event is departure
            Nd += 1
            
        else:
            No += 1                     # Increment observer counter if event is observation
            packets += (Na-Nd)          # Packets current in queue is total arrivals - total departures since packets can't be dropped
            if (Na == Nd):              # When arrivals = departures, queue is empty
                idle += 1       

    E_N = packets / No                  # Divide total packets seen in queue over observation events by number of observers
    P_IDLE = idle / No                  # Divide total amount of times queue was idle over observation events by number of observers

    # print(f"Final E[N]: {E_N}")
    # print(f"Final P_IDLE: {P_IDLE}")
    # print(f"Total Arrivals: {Na}")
    # print(f"Total Departures: {Nd}")
    # print(f"Total Observers: {No}")

    vals = [E_N, P_IDLE]

    return vals


def MM1K(rho, K):
    # Setup is the same as generate events function
    arrivalLambda = (rho * C)/L                
    observerLambda = 5 * arrivalLambda          
    arrivalTime = 0                             
    observerTime = 0                         
    events = []                                 

    # Same as generateEvents but since packets can be dropped we do not calculate departure times yet
    while arrivalTime < T:
        arrivalTime += getExponentialRV(arrivalLambda)
        heapq.heappush(events, (arrivalTime, 'a'))  # Push to heap which we will treat as how we will be grabbing events to check their type/time etc

    while observerTime < T:
        observerTime += getExponentialRV(observerLambda)
        heapq.heappush(events, (observerTime, 'o'))

    # Counters
    Na = 0                  
    Nd = 0                  
    No = 0                 
    idle = 0               
    generated = 0           # The total number of all packets generated regardless if it is dropped or not
    lost = 0                # Total number of packets dropped

    queueSize = 0           # Current number of packets in queue
    departureTime = 0       # Initiallize the departure time of the first packet since we will be calculating departure time as packets arrive 
    additiveQueueSize = 0;  # While question 6 does not ask for E[n] I kept this in anyways

    while len(events) > 0:  # Now we iterate over all events
        event = heapq.heappop(events)   # Pop the first event and check its type
        if (event[1] == 'a'):
            generated += 1
            currentEventTime = event[0]
            # If queue is full then drop the packet that just arrived
            if queueSize >= K:
                lost += 1
            # Add to queue if packet is not dropped and calculate the departure time
            else:
                Na += 1
                queueSize += 1 
                serviceTime = (getExponentialRV(1/L))/C     # Since we are not dropping the packet we need to generate its service time now
                if currentEventTime > departureTime:                    # Calculate departure time based off current event time
                    departureTime = currentEventTime + serviceTime
                else: 
                    departureTime += serviceTime
                
                heapq.heappush(events, (departureTime, 'd'))            # Since we know the packet is in the queue, we push the departure event to the heap

        # Departure events result in the queue size decreasing by one
        elif (event[1] == 'd'):
            Nd += 1
            queueSize -= 1

        elif (event[1] == 'o'):
            No += 1
            additiveQueueSize += Na - Nd    # Update additive queue size     
            # If arrivals and departures are equal then queue is empty
            if Na == Nd:
                idle += 1
    

    P_IDLE = idle / No              # Calculating P_IDLE the same as MM1
    P_LOSS = lost / generated       # P_LOSS is the number of packets dropped over total number of packets generated (packet arrivals)
    vals = [P_IDLE, P_LOSS]

    return vals

def generateEvents(rho):
    arrivalLambda = (rho * C)/L         # Calculating lambda with formula given in manual
    observerLambda = 5 * arrivalLambda  # Observer events should occur at 5x the rate of arrival events
    arrivalTime = 0                     # Start arrival time at 0
    departureTime = 0                   # Start departure time at 0
    events = []                         # The list that will store events and be sent to the M/M/1/K function

    while arrivalTime < T:              # Generate events until arrival times exceed sim time
        arrivalTime += getExponentialRV(arrivalLambda)  # Arrival time is an exponential variable as outlined in the lab manual
        events.append((arrivalTime, 'a'))               # Add this arrival event to the list
        serviceTime = (getExponentialRV(1/L))/C         # Calculate the service time
        # Checks whether the arrival time for an event will be serviced immediately or need to wait for the previous packet to depart
        if arrivalTime > departureTime:                 
            departureTime = arrivalTime + serviceTime
        else: 
            departureTime += serviceTime

        events.append((departureTime, 'd'))   # Add the departure event to the list

    observerTime = 0
     # Generate observer events independently since they are instantaneous and don't need departure/service times
    while observerTime < T:                            
        observerTime += getExponentialRV(observerLambda)
        events.append((observerTime, 'o', -1))
    
    events.sort(key=lambda x: x[0])                     # Sort the events list
    vals = MM1(events)                                  # Send sorted events list to the M/M/1 function
    return vals

def q3():
    E_N_List = []
    P_IDLE_List = []
    rhos = numpy.arange(0.35, 0.95, 0.1)    # Generate rhos in the range 0.25 - 0.95, incrementing by 0.1 each time

    # Call the event generator for each rho value with K = -1 which in my case indicates that the buffer is infinite
    for rho in rhos:
        ret_vals = generateEvents(rho)
        E_N_List.append(ret_vals[0])
        P_IDLE_List.append(ret_vals[1])

    pyplot.figure()
    pyplot.plot(rhos, E_N_List)
    pyplot.grid(True)
    pyplot.xlabel(r"$\rho$")
    pyplot.ylabel('E[n]')
    pyplot.title(r'Queue Packet Length (E[n]) vs Utilization ($\rho$)')
    pyplot.savefig('Q3_EN.png', dpi=300)

    pyplot.figure()
    pyplot.plot(rhos, P_IDLE_List)
    pyplot.grid(True)
    pyplot.xlabel(r"$\rho$")
    pyplot.ylabel('P_IDLE')
    pyplot.title(r'Queue Idle Time vs Utilization ($\rho$)')
    pyplot.savefig('Q3_IDLE.png', dpi=300)


def q4():
    # Call simulator with rho = 1.2
    generateEvents(1.2)   

def q5():
    # Call MM1K queue with rho = 1 and fixed buffer size
    MM1K(1, 5000)

def main():
    # q1()
    # generateEvents()
    q3()
    # q4()
    # q5()
    # q6 is below
    Q6 = False
    if __name__ == "__main__" and Q6 == True:
        multiprocessing.freeze_support()
        # Main simulation for different K values and plotting results
        P_LOSS_List = [[], [], []]  # 3 lists inside this list for K = 10, 25, 50
        P_IDLE_List = [[], [], []]
        rhos = numpy.arange(0.6, 1.6, 0.1)

        # Use ProcessPoolExecutor for multiprocessing (better for CPU-bound tasks)
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            for index, k in enumerate([10, 25, 50]):
                # Submit the simulator jobs to the executor
                future_to_rho = {executor.submit(MM1K, rho, k): rho for rho in rhos}
                
                # Collect results as they complete
                for future in concurrent.futures.as_completed(future_to_rho):
                    rho = future_to_rho[future]
                    try:
                        vals = future.result()
                        temp_idle = vals[0]
                        temp_loss = vals[1]
                        P_IDLE_List[index].append(temp_idle)
                        P_LOSS_List[index].append(temp_loss)
                    except Exception as exc:
                        print(f"Rho {rho} generated an exception: {exc}")

        pyplot.figure()
        for index, k in enumerate([10, 25, 50]):
            pyplot.plot(rhos, P_IDLE_List[index], label=f'K = {k}')
        pyplot.title(r'Queue Idle Time vs Utilization ($\rho$)')
        pyplot.xlabel(r'$\rho$')
        pyplot.ylabel('P_IDLE')
        pyplot.legend()
        pyplot.grid(True)
        pyplot.savefig('P_IDLE.png', dpi=300)

        pyplot.figure()
        for index, k in enumerate([10, 25, 50]):
            pyplot.plot(rhos, P_LOSS_List[index], label=f'K = {k}')
        pyplot.title(r'Probability of Packet Loss (P_LOSS) vs Utilization ($\rho$)')
        pyplot.xlabel(r'$\rho$')
        pyplot.ylabel('P_LOSS')
        pyplot.legend()
        pyplot.grid(True)
        pyplot.savefig('P_LOSS.png', dpi=300)



main()

