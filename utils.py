"""
    Collection of methods to help with inference and plotting
    for pymc3.

"""
import numpy as np

#import some special methods
from scipy.special import logit,expit
import scipy.stats as stats



def random_walk_prevalence(mu,sigma,initial_prevalence=0.01,shape=None):
    '''Create a random walk prevalence process with drift mu and variance sigma

    Parameters
    ----------
    mu : float
        drift of random walk in invlogit space
    sigma : float
        standard deviation of random walk in invlogit space
    shape : list
        shape of random walk in format (n_samples,n_months)

    Returns
    -------
    numpy array
        Samples of random walk process with shape (n_samples,n_months)

    '''

    # time-points and samples
    n_samples,n_months = shape


    # sample errors
    es = np.random.normal(loc=mu,scale=sigma,size=(n_samples,n_months))

    # create random walks with starting point equivalent to when prevalence is 0.01
    ws = logit(initial_prevalence) + np.cumsum(es,axis=1)

    # convert random walk into probability
    ps = expit(ws)

    return ps

def generate_data(N_mean = 10000, N_sd = 1000, p0 = 0.01, mu_w=1.,
                  sigma_w = 0.1, kappa_F = 0.25, kappa_N = 0.02, kappa_THN = 0.87,
                 p_d = 0.1):
    '''
    Generate sample data for fentanyl adulterant model with Take-home naloxone kits

    Parameters
    ----------
    N_mean : float
        mean of population
    N_sd : float
        sd of population
    p0 : float
        initial probability of fentanyl in supply
    mu_w : float
        drift of fentanyl (logit space)
    sigma_w : float
        scale of fentanyl (logit space)
    kappa_F : float
        probability of overdose on fentanyl
    kappa_N : float
        probability of overdose not on fentanyl
    kappa_THN : float
        probability of fentanyl use
    p_d : float
        probability of death following an overdose without intervention

    Returns
    -------

    Dictionary of observables for a single sample


    '''

    # simulate fentanyl in illicit drug supply
    pF = random_walk_prevalence(mu_w,sigma_w,initial_prevalence=p0,shape=(1,12))
    # calculate overdose rate
    od_rate = kappa_F*pF + kappa_N*(1-pF)

    # simulate a population size
    N = np.random.normal(loc=N_mean,scale=N_sd)

    # simulate kits distributed
    kits_distributed = np.cumsum(np.random.gamma(0.5,scale=300,size=(1,12)).round())

    # simulate kits used
    p_THN = kappa_THN*kits_distributed/N

    # death rate modified due to use of THN kits
    death_rate = (1. - p_THN)*p_d

    # simulate overdoses
    f_overdoses = np.random.binomial(N,kappa_F*pF)
    nf_overdoses = np.random.binomial(N,kappa_N*(1.-pF))

    overdoses = f_overdoses + nf_overdoses

    # simulate deaths
    f_deaths = np.random.binomial(f_overdoses,death_rate)
    nf_deaths = np.random.binomial(nf_overdoses,death_rate)
    deaths = f_deaths + nf_deaths

    # kits used
    kits_used = np.random.binomial(overdoses,p_THN)

    return {'overdoses': overdoses.flatten(),'probability fentanyl': pF.flatten(),
           'deaths': deaths.flatten(),'fentanyl deaths':f_deaths.flatten(),
            'kits distributed': kits_distributed.flatten(),
           'kits used':kits_used.flatten()}

def save_generate_data(data,filename='./data/data_sample.csv'):
    '''
    Save data to CSV file from output of generate_data

    Parameters
    ----------
    data : dict
         output of method generate_data
    filename : str
        filename to save to
    Returns
    -------
    None
    '''
    #add time
    n_months=12
    data['month'] = np.arange(1,n_months+1)

    df = pd.DataFrame(data)
    df[['month','overdoses','fentanyl deaths','deaths','kits distributed','kits used']].to_csv(filename,index=False)
