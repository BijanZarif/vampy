# -*- coding: utf-8 -*-

from __future__ import division

import numpy as np
import sys
import matplotlib.pylab as plt

from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm


class Artery(object):
    """
    Class representing an artery.
    """
        
        
    def __init__(self, pos, R, lam, rho, nu, delta, **kwargs):
        self._pos = pos
        self._A0 = np.pi*R*R
        self._L = R[0]*lam
        k = kwargs['k']
        Ehr = k[0] * np.exp(k[1]*R) + k[2]
        self._f = 4 * Ehr/3
        self._df = 4/3 * k[0] * k[1] * np.exp(k[1]*R)     
        self._nu = nu
        nondim = kwargs['nondim']
        self._Re = nondim[2]
        self._delta = delta
        self._depth = kwargs['depth']
        
        
    def initial_conditions(self, u0, ntr):
        if not hasattr(self, '_nx'):
            raise AttributeError('Artery not meshed. Execute mesh(self, nx) \
before setting initial conditions.')
        self.U = np.zeros((2, ntr, self.nx))
        self.P = np.zeros((ntr, self.nx))
        self.U0 = np.zeros((2, self.nx))
        self.U0[0,:] = self.A0
        self.U0[1,:].fill(u0)
        
        
    def mesh(self, nx):
        self._nx = nx
        x = np.linspace(0.0, self.L, nx)
        self._dx = x[1] - x[0]
        R = np.sqrt(self.A0/np.pi)
        #self._xgrad = R * np.log(R[-1]/R[0]) / self.L
        self._xgrad = np.gradient(R, 2*self.dx)
        
        
    def p(self, a):
        return self.f * (1 - np.sqrt(self.A0/a))
        

    def wave_speed(self, a):
        Ehr = 3/4 * self.f
        return -np.sqrt(2/3 * Ehr * np.sqrt(self.A0/a))
        
        
    def F(self, U, **kwargs):
        a, q = U
        out = np.zeros(U.shape)
        out[0] = q
        if 'j' in kwargs:
            j = kwargs['j']
            a0 = self.A0[j]
            f = self.f[j]
        elif 'k' in kwargs:
            j = kwargs['j']
            k = kwargs['k']
            a0 = self.A0[j:k]
            f = self.f[j:k]
        else:
            raise IndexError("Required to supply at least one index in function F.")
        out[1] = q*q/a + f * np.sqrt(a0*a)
        return out
        
        
    def S(self, U, **kwargs):
        a, q = U
        out = np.zeros(U.shape)
        if 'j' in kwargs:
            j = kwargs['j']
            a0 = self.A0[j]
            xgrad = self.xgrad[j]
            f = self.f[j]
            df = self.df[j]
        elif 'k' in kwargs:
            j = kwargs['j']
            k = kwargs['k']
            a0 = self.A0[j:k]
            xgrad = self.xgrad[j:k]
            f = self.f[j:k]
            df = self.df[j:k]
        else:
            raise IndexError("Required to supply at least one index in function S.")
        R = np.sqrt(a/np.pi)
        out[1] = -2*np.pi*R*q/(self.Re*self.delta*a) +\
                (2*np.sqrt(a) * (np.sqrt(np.pi)*f +\
                np.sqrt(a0)*df) - a*df) * xgrad
        return out
        
        
    def dBdx(self, l, xi):
        if l == self.L+self.dx/2:
            x_0 = self.x[-2]
            x_1 = self.x[-1]
            f_0 = self.f[-2]
            f_1 = self.f[-1]
            A0_0 = self.A0[-2]
            A0_1 = self.A0[-1]
        else:
            x_0 = self.x[1]
            x_1 = self.x[0]
            f_0 = self.f[1]
            f_1 = self.f[0]
            A0_0 = self.A0[1]
            A0_1 = self.A0[0]
        f_l = utils.extrapolate(l, [x_0, x_1], [f_0, f_1])    
        A0_l = utils.extrapolate(l, [x_0, x_1], [A0_0, A0_1])   
        return f_l/2 * np.sqrt(A0_l/xi)
        
        
    def dBdxdxi(self, l, xi):
        if l == self.L+self.dx/2:
            x_0 = self.x[-2]
            x_1 = self.x[-1]
            f_0 = self.f[-2]
            f_1 = self.f[-1]
            df_0 = self.df[-2]
            df_1 = self.df[-1]
            A0_0 = self.A0[-2]
            A0_1 = self.A0[-1]
            xgrad_0 = self.xgrad[-2]
            xgrad_1 = self.xgrad[-1]
        else:
            x_0 = self.x[1]
            x_1 = self.x[0]
            f_0 = self.f[1]
            f_1 = self.f[0]
            df_0 = self.df[1]
            df_1 = self.df[0]
            A0_0 = self.A0[1]
            A0_1 = self.A0[0]
            xgrad_0 = self.xgrad[1]
            xgrad_1 = self.xgrad[0]
        f_l = utils.extrapolate(l, [x_0, x_1], [f_0, f_1])   
        df_l = utils.extrapolate(l, [x_0, x_1], [df_0, df_1])   
        A0_l = utils.extrapolate(l, [x_0, x_1], [A0_0, A0_1])   
        xgrad_l = utils.extrapolate(l, [x_0, x_1], [xgrad_0, xgrad_1]) 
        return (1/(2*np.sqrt(xi)) * (f_l*np.sqrt(np.pi) +\
                                    df_l*np.sqrt(A0_l)) - df_l) * xgrad_l
                                    
                                    
    def dFdxi2(self, l, xi1, xi2):
        if l == self.L+self.dx/2:
            x_0 = self.x[-2]
            x_1 = self.x[-1]
            R0_0 = np.sqrt(self.A0[-2]/np.pi)
            R0_1 = np.sqrt(self.A0[-1]/np.pi)
        else:
            x_0 = self.x[1]
            x_1 = self.x[0]
            R0_0 = np.sqrt(self.A0[1]/np.pi)
            R0_1 = np.sqrt(self.A0[0]/np.pi)
        R0_l = utils.extrapolate(l, [x_0, x_1], [R0_0, R0_1])
        return 2*np.pi*R0_l*xi1/(self.delta*self.Re*xi2**2)
        
        
    def dFdxi1(self, l, xi1, xi2):
        if l == self.L+self.dx/2:
            x_0 = self.x[-2]
            x_1 = self.x[-1]
            R0_0 = np.sqrt(self.A0[-2]/np.pi)
            R0_1 = np.sqrt(self.A0[-1]/np.pi)
        else:
            x_0 = self.x[1]
            x_1 = self.x[0]
            R0_0 = np.sqrt(self.A0[1]/np.pi)
            R0_1 = np.sqrt(self.A0[0]/np.pi)
        R0_l = utils.extrapolate(l, [x_0, x_1], [R0_0, R0_1])
        return 2*np.pi*R0_l/(self.delta*self.Re*xi2)
        
        
    def dpdx(self, l, xi):
        if l == self.L+self.dx/2:
            x_0 = self.x[-2]
            x_1 = self.x[-1]
            f_0 = self.f[-2]
            f_1 = self.f[-1]
            A0_0 = self.A0[-2]
            A0_1 = self.A0[-1]
        else:
            x_0 = self.x[1]
            x_1 = self.x[0]
            f_0 = self.f[1]
            f_1 = self.f[0]
            A0_0 = self.A0[1]
            A0_1 = self.A0[0]
        f_l = utils.extrapolate(l, [x_0, x_1], [f_0, f_1])   
        A0_l = utils.extrapolate(l, [x_0, x_1], [A0_0, A0_1])   
        return -f_l/2 * np.sqrt(A0_l/xi**3)
        

    def solve(self, lw, U_in, U_out, t, dt, save, i):
        # solve for current timestep
        U1 = lw.solve(self.U0, U_in, U_out, t, self.F, self.S, dt)
        np.copyto(self.U0, U1)
        if save:
            self.P[i,:] = self.p(U1[0,:])
            np.copyto(self.U[:,i,:], U1)
        
        
    def dump_results(self, suffix, data_dir):
        np.savetxt("%s/u%d_%s.csv" % (data_dir, self.pos, suffix),
                   self.U[1,:,:], delimiter=',')
        np.savetxt("%s/a%d_%s.csv" % (data_dir, self.pos, suffix),
                   self.U[0,:,:], delimiter=',')  
        np.savetxt("%s/p%d_%s.csv" % (data_dir, self.pos, suffix),
                   self.P, delimiter=',') 
                   
                   
    def spatial_plots(self, suffix, plot_dir, n):
        # redimensionalise
        nt = len(self.U[0,:,0])    
        x = np.linspace(0, self.L, self.nx)
        skip = int(nt/n)
        u = ['a', 'q', 'p']
        l = ['m^2', 'm^3/s', 'mmHg']
        positions = range(0,nt-1,skip)
        #positions = range(5)
        for i in range(2):
            y = self.U[i,positions,:]
            fname = "%s/%s_%s%d_spatial.png" % (plot_dir, suffix, u[i], self.pos)
            Artery.plot(suffix, plot_dir, x, y, positions, "m", l[i],
                        fname)
                     
        y = self.P[positions,:] # convert to mmHg    
        fname = "%s/%s_%s%d_spatial.png" % (plot_dir, suffix, u[2], self.pos)
        Artery.plot(suffix, plot_dir, x, y, positions, "m", l[2],
                        fname)
            
            
    def time_plots(self, suffix, plot_dir, n, time):
        nt = len(time)
        skip = int(self.nx/n)
        u = ['a', 'q', 'p']
        l = ['m^2', 'm^3/s', 'mmHg']
        positions = range(0,self.nx-1,skip)
        #positions = range(0,5)        
        for i in range(2):
            y = self.U[i,:,positions]
            fname = "%s/%s_%s%d_time.png" % (plot_dir, suffix, u[i], self.pos)
            Artery.plot(suffix, plot_dir, time, y, positions, "t", l[i],
                        fname)
                        
        y = np.transpose(self.P[:,positions])   
        fname = "%s/%s_%s%d_time.png" % (plot_dir, suffix, u[2], self.pos)
        Artery.plot(suffix, plot_dir, time, y, positions, "t", l[2],
                        fname)
            
            
    @staticmethod            
    def plot(suffix, plot_dir, x, y, labels, xlabel, ylabel, fname):
        plt.figure(figsize=(10,6))
        s = y.shape
        n = min(s)
        for i in range(n):
            plt.plot(x, y[i,:], label="%d" % (labels[i]), lw=2)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.legend()
        plt.savefig(fname, dpi=600, bbox_inches='tight')
        
        
    def p3d_plot(self, suffix, plot_dir, time):
        fig = plt.figure(figsize=(10,6))
        ax = fig.gca(projection='3d')
        x = np.linspace(0, self.L, len(time))
        Y, X = np.meshgrid(time, x)
        dz = int(self.nx/len(time))
        Z = self.P[:,0:self.nx+1:dz]
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)
        fig.colorbar(surf, shrink=0.5, aspect=5)
        fname = "%s/%s_p3d%d.png" % (plot_dir, suffix, self.pos)
        fig.savefig(fname, dpi=600, bbox_inches='tight')
        
        
    def q3d_plot(self, suffix, plot_dir, time):
        fig = plt.figure(figsize=(10,6))
        ax = fig.gca(projection='3d')
        x = np.linspace(0, self.L, len(time))
        Y, X = np.meshgrid(time, x)
        dz = int(self.nx/len(time))
        Z = self.U[1,:,0:self.nx+1:dz]
        surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                       linewidth=0, antialiased=False)
        fig.colorbar(surf, shrink=0.5, aspect=5)
        fname = "%s/%s_q3d%d.png" % (plot_dir, suffix, self.pos)
        fig.savefig(fname, dpi=600, bbox_inches='tight')
        
    
    @property
    def pos(self):
        return self._pos
    
    @property
    def R(self):
        return self._R
        
    @property
    def A0(self):
        return self._A0
        
    @property
    def L(self):
        return self._L
        
    @property
    def f(self):
        return self._f

    @property
    def df(self):
        return self._df
        
    @property
    def rho(self):
        return self._rho
        
    @property
    def nu(self):
        return self._nu
        
    @property
    def init_cond(self):
        return self._init_cond
        
    @property
    def dx(self):
        return self._dx

    @property
    def nx(self):
        return self._nx
        
    @property
    def U0(self):
        return self._U0
        
    @U0.setter
    def U0(self, value): 
        self._U0 = value
        
    @property
    def U(self):
        return self._U
        
    @U.setter
    def U(self, value): 
        self._U = value
        
    @property
    def P(self):
        return self._P
        
    @P.setter
    def P(self, value): 
        self._P = value
        
    @property
    def Re(self):
        return self._Re
        
    @property
    def delta(self):
        return self._delta
        
    @property
    def xgrad(self):
        return self._xgrad
        
    @property
    def depth(self):
        return self._depth