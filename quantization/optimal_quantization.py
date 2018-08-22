"""
Optimal quantization of the empirical distribution of a dataset -

The algorithm finds an optimal aproximation of the dataset by a
smaller number n of points, and yields a K-means type clustering.
The n points of the approximation, weighted by the masses of their
Voronoi cells, define a discrete distribution that best approximates,
in the sense of the Wasserstein distance and at fixed support size n,
the empirical distribution of the dataset. The Voronoi diagram associated
to these points yields a K-means type clustering of the dataset.
"""

import numpy as np
from geomstats.hypersphere import HypersphereMetric


TOLERANCE = 1e-5
IMPLEMENTED = ('S1', 'S2')


def sample_from(points, size=1):
    """
    Sample from the empirical distribution associated to points.
    """
    n_points = points.shape[0]
    dimension = points.shape[-1]

    index = np.random.randint(low=0, high=n_points, size=size)
    sample = points[np.ix_(index, np.arange(dimension))]

    return sample


def closest_neighbor(point, neighbors, space=None):
    """
    Find closest neighbor of point among neighbors.
    """
    if space not in IMPLEMENTED:
        raise NotImplementedError(
                'The closest neighbor function is not implemented'
                ' for space {}. The spaces available'
                ' are: {}.'.format(space, IMPLEMENTED))
    elif space == 'S1':
        metric = HypersphereMetric(dimension=1)
    else:
        metric = HypersphereMetric(dimension=2)

    dist = metric.dist(point, neighbors)
    index_closest_neighbor = dist.argmin()

    return index_closest_neighbor


def diameter_of_data(points, space=None):
    """
    Compute the two points that are farthest away from each other in points.
    """
    if space not in IMPLEMENTED:
        raise NotImplementedError(
                'The diameter function is not implemented'
                ' for space {}. The spaces available'
                ' are: {}.'.format(space, IMPLEMENTED))
    elif space == 'S1':
        metric = HypersphereMetric(dimension=1)
    else:
        metric = HypersphereMetric(dimension=2)

    diameter = 0.0
    n_points = points.shape[0]

    for i in range(n_points-1):
        dist_to_neighbors = metric.dist(points[i, :], points[i+1:, :])
        dist_to_farthest_neighbor = dist_to_neighbors.max()
        diameter = np.maximum(diameter, dist_to_farthest_neighbor * 2)

    return diameter


def karcher_flow(points, space=None, tolerance=TOLERANCE):
    """
    Compute the Karcher mean of points using a Karcher flow algorithm.
    Return :
        - the karcher mean
        - the number of steps needed to converge.
    """
    if space not in IMPLEMENTED:
        raise NotImplementedError(
                'The Karcher mean function is not implemented'
                ' for space {}. The spaces available for Karcher flow'
                ' are: {}.'.format(space, IMPLEMENTED))
    elif space == 'S1':
        metric = HypersphereMetric(dimension=1)
    else:
        metric = HypersphereMetric(dimension=2)

    karcher_mean = sample_from(points)

    n_points = points.shape[0]
    gap = 1.0
    step = 0
    while gap > tolerance:
        tangent_vectors = np.zeros(points.shape)

        for i in range(n_points):
            tangent_vectors[i, :] = metric.log(points[i, :], karcher_mean)

        tan_vec_update = np.sum(tangent_vectors, axis=0) / n_points
        karcher_mean_updated = metric.exp(tan_vec_update, karcher_mean)

        gap = metric.dist(karcher_mean, karcher_mean_updated)
        karcher_mean = karcher_mean_updated
        step += 1

    return karcher_mean, step


def optimal_quantization(points, n_centers=10, space=None, n_repetition=20,
                         tolerance=TOLERANCE):
    """
    Compute the optimal approximation of points by a smaller number
    of weighted centers using the Competitive Learning Riemannian
    Quantization algorithm. Returns :
        - n_centers centers
        - n_centers weights between 0 and 1
        - an array containing the labels of a clustering
        - the number of steps needed to converge.
    """
    if space not in IMPLEMENTED:
        raise NotImplementedError(
                'The optimal quantization function is not implemented'
                ' for space {}. The spaces available for quantization'
                ' are: {}.'.format(space, IMPLEMENTED))
    elif space == 'S1':
        metric = HypersphereMetric(dimension=1)
    else:
        metric = HypersphereMetric(dimension=2)

    # random initialization of the centers
    centers = sample_from(points, n_centers)

    gap = 1.0
    step = 0

    while gap > tolerance:
        step += 1
        k = np.floor(step / n_repetition) + 1

        sample = sample_from(points)

        index = closest_neighbor(sample, centers, space)
        center_to_update = centers[index, :]

        tan_vec_update = metric.log(sample, center_to_update) / (k+1)
        new_center = metric.exp(tan_vec_update, center_to_update)
        gap = metric.dist(center_to_update, new_center)
        gap = (gap != 0) * gap + (gap == 0)

        centers[index, :] = new_center

    n_points = points.shape[0]
    clustering = np.zeros((n_points,))
    weights = np.zeros((n_centers,))

    for i, point in enumerate(points):
        index = closest_neighbor(point, centers, space)
        clustering[i] = index
        weights[index] += 1

    weights = weights / n_points

    return centers, weights, clustering, step
