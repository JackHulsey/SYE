# this is where we will calculate the frobenius norm and fixed point integrals
import numpy as np
from scipy.linalg import lu, solve


# functions used for method 1

def frobenius_norm(r):
    '''
    Frobenius norm of a matrix
    :param r: matrix we're passing in
    :return: square root of the sum of all entries squared
    '''
    sum = 0
    for v in r:
        sum += (v*v)
    return np.sqrt(sum)

def fixed_point(A, records, eps=1e-1000):
    '''
    Calculate the fixed point integral of a matrix
    :param A: matrix we're integrating
    :param records: records of the teams to make sure we're going to make the array the right length
    :param eps: the closeness of the values
    :return: the ranking array
    '''
    all_ranks = []
    r_0 = np.ones(len(records))
    A_r = A.dot(r_0)
    denominator = frobenius_norm(A_r)
    A_r /= denominator
    n = 2
    while True:
        A_r = (A.dot(A_r))
        denominator = frobenius_norm(A_r)
        A_r /= denominator
        all_ranks.append(A_r)
        if np.allclose(r_0, A_r, eps):
          break
        r_0 = A_r

        n += 1
        r = A_r
    return r, n, all_ranks

# strength = (1/num_games) * (sum ai*ranking)
def linear_strengths(matrix, ranking, records):
    '''
    Calculate the strengths based off a ranking array (figure 2.1)
    :param matrix: current matrix we're working with
    :param ranking: ranking vector
    :param records: records of the teams
    :return: the vector of strengths
    '''
    strength = []
    sum = 0
    for i in range(len(records)):
        for j in range(len(records)):
          # multiplies 1 or 0 with that teams ranking
          sum += matrix[i][j]*ranking[j]
          # print(matrix[iter][i], rankings[i])
        # print(sum, records[i][4])
        sum /= (records[i][4])
        strength.append(sum)
        sum = 0
    return strength

def output(ranking, records, limit=100, strength=None):
    s = np.argsort(-ranking)
    iter = 1
    tmp = s[0]
    for num in s:
        if strength is not None:
            # output with strengths
            print(f"{iter:<3} {records[num][0]:<20} {round(strength[num], 6):<10} {round(strength[tmp] - strength[num], 5)}")
        else:
            # output with records of win-loss-tie
            print(f"{iter:<3} {records[num][0]:<18} {records[num][1]}-{records[num][2]}-{records[num][5]} {ranking[num]}")
        if iter == limit:
            return
        iter += 1
        tmp = num

# functions needed for method 2

# 3.4 in the paper
def f(x):
  result = (0.05*x + x*x) / (2 + 0.05*x + x*x)
  return result

# 3.5
def e(s1, s2):
  result = (5 + s1 + pow(s1, (2/3))) / (5 + s2 + pow(s1, (2/3)))
  return result

def F(matrix, ranking, records):
    '''
    Calculate the strengths based off a ranking array (figure 3.2)
    :param matrix: current matrix we're working with
    :param ranking: ranking vector
    :param records: records of the teams
    :return: the vector of strengths
    '''
    ranks = []
    sum = 0
    for i in range(len(records)):
        for j in range(len(records)):
          if int(matrix[i][j]) == 0 and int(matrix[j][i]) == 0:
              continue
          # inputs the score of the games into the function to calculate e
          e_ij = e(int(matrix[i][j]), int(matrix[j][i]))

          # uses e_ij multiplied by the ranking of the opponent to calculate the strengths
          sum += f(e_ij*ranking[j])

        sum /= (records[i][4]) # divide by number of games
        ranks.append(sum)
        sum = 0
    return ranks

def nonlinear_strengths(matrix, records):
    # repeatedly calls F on ranking vector r until r stabilizes
    all_ranks = []
    r_0 = np.ones(len(records))
    n = 1
    while True:
        r = F(matrix, r_0, records)
        all_ranks.append(r)
        if np.allclose(r_0, r, 1e-10):
             break
        r_0 = r
        n += 1
    # returns ranking vector, number of iterations, and array of all ranking vectors
    return r, n, all_ranks

# functions needed for method 3

def pi_ij(s1, s2):
    return s1 / (s1 + s2)

def diagonal_entries(i, matrix, n):
    total = 0
    for j in range(n):
        total += (matrix[i][j]**2)

    return total

def make_B_matrix(records, score_matrix):
    # Initialize square matrix for results
    n = len(records)
    matrix = [[0] * n for _ in range(n)]

    # Fill the matrix with match result
    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = diagonal_entries(i, score_matrix, n)  # A team doesn't play against itself
            else:
                matrix[i][j] = -1 * (score_matrix[i][j]*score_matrix[j][i])
    return matrix

def inverse_power_method(B, eps=1e-1000):
    # Initial guess for the eigenvector (random)

    n = B.shape[0]
    r = np.ones(n)
    # Normalize the initial guess
    r = r / np.linalg.norm(r)

    # LU decomposition of matrix A
    P, L, U = lu(B)

    iter = 0
    while True:
        # Solve the system using forward and backward substitution
        y = solve(L, r)  # Forward substitution
        r_0 = solve(U, y)  # Backward substitution

        # Normalize the vector to avoid overflow/underflow
        r_0 = r_0 / np.linalg.norm(r_0)

        # Check for convergence
        if np.allclose(r_0, r, eps):
            break

        r = r_0
        iter += 1

    # The result is the eigenvector corresponding to the smallest eigenvalue
    return r_0, iter


def inverse_power_method_two(B, A0, max_iter=1000, tol=1e-8):
    """
    Inverse Power Method to find the eigenvector corresponding to the smallest eigenvalue
    of the matrix B' = B + A0 * I using LU decomposition.

    Args:
    - B (ndarray): The matrix B (n x n).
    - A0 (float): The scalar A0.
    - max_iter (int): Maximum number of iterations.
    - tol (float): Tolerance for convergence.

    Returns:
    - eigvec (ndarray): The eigenvector corresponding to the smallest eigenvalue of B'.
    """
    # Define matrix B' = B + A0 * I
    n = B.shape[0]
    B_prime = B + A0 * np.eye(n)

    # Perform LU decomposition of B'
    P, L, U = lu(B_prime)

    # Initial guess for the eigenvector (random vector)
    eigvec = np.ones(n)

    for _ in range(max_iter):
        # Solve the system B' * eigvec = eigvec using forward and backward substitution
        # First solve L * y = eigvec using forward substitution
        y = np.linalg.solve(L, eigvec)

        # Then solve U * eigvec = y using backward substitution
        eigvec = np.linalg.solve(U, y)

        # Normalize the eigenvector
        eigvec_norm = np.linalg.norm(eigvec)
        eigvec /= eigvec_norm

        # Check for convergence (if the change in the eigenvector is small)
        if np.linalg.norm(np.dot(B_prime, eigvec) - eigvec) < tol:
            break
        iter = _
    # Return the eigenvector corresponding to the smallest eigenvalue
    return eigvec, iter