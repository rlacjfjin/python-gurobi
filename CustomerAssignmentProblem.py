import random
import gurobipy as grb
import matplotlib.pyplot as plt
import numpy as np
from sklearn import cluster

def data_generate(seed,num_customers,num_candidates,num_gaussians):
    random.seed(seed)
    customers_per_gaussian = np.random.multinomial(num_customers,
                                               [1/num_gaussians]*num_gaussians)
    customer_locs = []
    for i in range(num_gaussians):
        # each center coordinate in [-0.5, 0.5]
        center = (random.random()-0.5, random.random()-0.5)
        customer_locs += [(random.gauss(0,.1) + center[0], random.gauss(0,.1) + center[1])
                      for i in range(customers_per_gaussian[i])]
    # each candidate coordinate in [-0.5, 0.5]
    facility_locs = [(random.random()-0.5, random.random()-0.5)
                  for i in range(num_candidates)]
    return customer_locs,facility_locs

def preprocessing(customer_locs):
    kmeans = cluster.MiniBatchKMeans(n_clusters=num_clusters, init_size=3*num_clusters,
                         random_state=seed).fit(customer_locs)
    memberships = list(kmeans.labels_)
    centroids = list(kmeans.cluster_centers_) # Center point for each cluster
    weights = list(np.histogram(memberships, bins=num_clusters)[0]) # Number of customers in each cluster
    return centroids,weights

def dist(loc1, loc2):
    return np.linalg.norm(loc1-loc2, ord=2) # Euclidean distance

def get_pairings(facility_locs,centroids):
    pairings = {(facility, cluster): dist(facility_locs[facility], centroids[cluster])
                for facility in range(num_candidates)
                for cluster in range(num_clusters)
                if  dist(facility_locs[facility], centroids[cluster]) < threshold}
    return pairings

def Facilitylocation(num_candidates,max_facilities,pairings,num_clusters,weights):
    model = grb.Model("Facility location")
    select = model.addVars(range(num_candidates), vtype=grb.GRB.BINARY, name='select')
    assign = model.addVars(pairings.keys(), vtype=grb.GRB.BINARY, name='assign')
    obj = grb.quicksum(weights[cluster]
                      * pairings[facility, cluster]
                      * assign[facility, cluster]
                      for facility, cluster in pairings.keys())
    model.setObjective(obj, grb.GRB.MINIMIZE)
    model.addConstr(select.sum() <= max_facilities, name="Facility_limit")
    model.addConstrs((assign[facility, cluster] <= select[facility]
                  for facility, cluster in pairings.keys()),name="Open2assign")
    model.addConstrs((assign.sum('*', cluster) == 1
                  for cluster in range(num_clusters)),name="Closest_store")

    model.optimize()
    assignments = [p for p in pairings if assign[p].x > 0.5]
    return assignments

def plot_result(assignments):
    plt.figure(figsize=(8, 8), dpi=150)
    plt.scatter(*zip(*customer_locs), c='Pink', s=0.5)
    plt.scatter(*zip(*centroids), c='Red', s=10)
    plt.scatter(*zip(*facility_locs), c='Green', s=10)
    for p in assignments:
        pts = [facility_locs[p[0]], centroids[p[1]]]
        plt.plot(*zip(*pts), c='Black', linewidth=0.1)
    plt.show()


if __name__ == '__main__':
    seed = 10101
    num_customers = 50000
    num_candidates = 50
    max_facilities = 8
    num_clusters = 1000
    num_gaussians = 10
    threshold = 0.99
    ## 随机生成客户和工厂
    customer_locs,facility_locs = data_generate(seed,num_customers,num_candidates,num_gaussians)
    ## preprocessing
    centroids,weights = preprocessing(customer_locs)
    pairings = get_pairings(facility_locs,centroids)
    #求解模型
    assignments = Facilitylocation(num_candidates, max_facilities, pairings, num_clusters, weights)
    plot_result(assignments)