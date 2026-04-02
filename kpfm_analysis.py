import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import lmfit
from statsmodels.stats.stattools import durbin_watson


class KPFMSpectrumAnalysis():

    def __init__(self, bias, df):
        self.bias = bias
        self.df = df


    def CalcVContact(self, aGuess=0.0, bGuess=0.0, cGuess=0.0, error=False):
        """
        Contact potential calculation. Involves performing a parabolic fit, ax**2 + bx + c, on
        the KPFM spectra data, and finding the fit's minimum.
        @param aGuess: Initial guess for the fitting parameter a. The default is 0.
        @type aGuess: float, optional
        @param bGuess: Initial guess for the fitting parameter b. The default is 0.
        @type bGuess: float, optional
        @param cGuess: Initial guess for the fitting parameter c. The default is 0.
        @type cGuess: float, optional
        @param error: Whether to report the estimated error on Vcontact. Found by
        propagating the estimates error found for the fitting parameters, a, b, and c.
        @type error: float, optional
        @return: (Calculated Vcontact, estimated error on Vcontact if error==True)
        @rtype: (float, float)
        The class instance will have added attributes, including the found
        fit and its residuals, so we can get a measure of the confidence to have
        in our result eg. using the PlotVContactCalculation method below.
        """
        self.ParabolaFit(aGuess=aGuess, bGuess=bGuess, cGuess=cGuess)
        self.ParabolaMinima()
        if error == True:
            return self.vContact, self.vContactErr
        else:
            return self.vContact

    def ParabolaFit(self, aGuess=0.0, bGuess=0.0, cGuess=0.0):
        """
        Parabolic fit, ax**2 + bx + c.
        @param aGuess: Initial guess for the fitting parameter a. The default is 0.
        @type aGuess: float, optional
        @param bGuess: Initial guess for the fitting parameter b. The default is 0.
        @type bGuess: float, optional
        @param cGuess: Initial guess for the fitting parameter c. The default is 0.
        @type cGuess: float, optional
        @return: (fit, fitInfo)
        @rtype: (arr, Lmfit ModelResult instance which contains the found fitting parameters,
         residuals... See lmfit’s ModelResult documentation for more info.)
        """

        def Parabola(x, a, b, c):
            return a * x ** 2 + b * x + c

        x, y = self.bias, self.df

        parabola_params = lmfit.Parameters()  # define a python dict to store the fitting parameters

        # define the fitting parameters and an initial guess for its value.
        # Here you can also define contraints, and other useful things.
        parabola_params.add('a', value=aGuess)
        parabola_params.add('b', value=bGuess)
        parabola_params.add('c', value=cGuess)

        model = lmfit.Model(Parabola, independent_vars='x', param_names=['a', 'b', 'c'])
        fitInfo = model.fit(y, params=parabola_params, x=x)

        # The found fitting parameters are stored in the fitInfo object
        a, b, c = fitInfo.params['a'].value, fitInfo.params['b'].value, fitInfo.params['c'].value

        # Evaluate the found fit for our x values
        fit = Parabola(x, a, b, c)

        # calclate the fit's confidence band to 2 sigma, ie ~95%. fit +/- fitConfBand.
        fitConfBand = fitInfo.eval_uncertainty(params=fitInfo.params, sigma=2)

        self.fitConfBand = fitConfBand
        self.fit = fit
        self.fitInfo = fitInfo
        self.meanAbsRes = np.mean(np.absolute(fitInfo.residual))
        self.fitA = a
        self.fitB = b
        self.fitC = c

        dw = durbin_watson(fitInfo.residual)

        self.dw_parabola = dw

        return fit, fitInfo

    def excitationLinearFit(self, x_control, y_control):
        """
        Parabolic fit, ax**2 + bx + c.
        @param aGuess: Initial guess for the fitting parameter a. The default is 0.
        @type aGuess: float, optional
        @param bGuess: Initial guess for the fitting parameter b. The default is 0.
        @type bGuess: float, optional
        @param cGuess: Initial guess for the fitting parameter c. The default is 0.
        @type cGuess: float, optional
        @return: (fit, fitInfo)
        @rtype: (arr, Lmfit ModelResult instance which contains the found fitting parameters,
         residuals... See lmfit’s ModelResult documentation for more info.)
        """
        x, y = x_control, y_control

        model = lmfit.models.LinearModel()
        params = model.guess(y, x=x)

        params['intercept'].set(value=np.average(y), vary=True)
        params['slope'].set(value=0, vary=False)

        fitInfo = model.fit(y, x=x, params=params)

        fit = fitInfo.best_fit

        # self.meanAbsResControl = np.mean(np.absolute(fitInfo.residual))
        # c = fitInfo.params['intercept'].value
        dw_excitation = durbin_watson(fitInfo.residual)

        self.dw_excitation = dw_excitation

        """
        #fig, ax = plt.subplots(2, sharex=True)
        ax1.plot(x, y-c, 'k')
        ax1.plot(x, fit-c, c='tab:red', label='flat line fit')
        #ax1.plot(x, fitInfo.residual, c='gray')
        ax2.plot(x, np.absolute(fitInfo.residual), '.', c='gray')
        ax2.scatter(np.mean(x), self.meanAbsResControl, s=50, marker='*', c='tab:orange', zorder=2, label='mean abs res')
        ax2.set_title('DW stat: ' + str(round(dw,3)))
        ax1.grid()
        ax2.grid()
        print(lmfit.fit_report(fitInfo))

        """

    def ParabolaMinima(self):
        """
        The parabolic fit's minima.
        @return: (xMin, yMin, xMinErr, yMinErr) of the parabolic fit. errors derived from the fitting parameters'
        error, as calculated by lmfit
        Note: we suspect lmfit's errors are an underestimate!
        @rtype: (float, float, float, float)
        """
        # Get the best-fitting paramenters
        a, b, c = self.fitInfo.params['a'].value, self.fitInfo.params['b'].value, self.fitInfo.params['c'].value

        # Get the estimated standard error for the best-fitting paramenters
        aErr, bErr, cErr = self.fitInfo.params['a'].stderr, self.fitInfo.params['b'].stderr, self.fitInfo.params[
            'c'].stderr

        # Calculate the best-fit's minima
        xMin = -b / (2 * a)
        yMin = c - b ** 2 / (4 * a)

        # Calculate the error on the best-fit's minima
        xMinErr = 0.5 * np.sqrt(((bErr ** 2) * (a ** 2) + (b ** 2) * (aErr ** 2)) / (a ** 4))
        yMinErr = 0.25 * np.sqrt(
            (b ** 4 * aErr ** 2 + 4 * b ** 2 * a ** 2 * bErr ** 2 + 16 * cErr ** 2 * a ** 4) / a ** 4)

        self.vContact = xMin
        self.dfAtVContact = yMin
        self.vContactErr = xMinErr
        self.dfAtVContactErr = yMinErr

        return xMin, yMin, xMinErr, yMinErr


    def PlotVContactCalculation(self, axFit=None, axResiduals=None):
        """
        Visualise the self.ParabolaFit() and self.ParabolaMinima() calculation with a
        plot showing the spectrum data, the parabolic fit, the fit's minima (ie.
        the calculated contact potential), the fits 2 sigma confidence band, and the fit's residuals.
        @param axFit: axes for the fit's plot
        @type axFit: matplotlib Axes instance, optional
        @param axResiduals: axes for the residuals' plot
        @type axResiduals: matplotlib Axes instance, optional
        @return: figure and its axes
        @rtype: a matplotlib Figure and two Axes objects
        """
        # if the contact potential has not yet been calculated, calculate it.
        if not hasattr(self, 'vContact'): self.CalcVContact()

        if axFit == None and axResiduals == None:
            fig, [axFit, axResiduals] = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(7, 6))
        elif axFit == None and axResiduals != None:
            fig, axFit = plt.subplots()
        elif axFit != None and axResiduals == None:
            fig, axResiduals = plt.subplots()

        axFit.plot(self.bias, self.df, label='data', color='black')
        axFit.plot(self.bias, self.fit, label=' parabolic fit', color='red')
        axFit.errorbar(self.vContact, self.dfAtVContact, xerr=self.vContactErr, yerr=self.dfAtVContactErr,
                       color='black')
        axFit.fill_between(self.bias, self.fit - self.fitConfBand,
                           self.fit + self.fitConfBand, color='red', alpha=0.2, label=r'confidence band, 2$\sigma$')
        axFit.plot(self.vContact, self.dfAtVContact, "*", color='orange', markersize=10,
                   label='$V_{Contact}$, ' + str(round(self.vContact, ndigits=2)) + r'V $\pm $ ' + str(
                       round(self.vContactErr, ndigits=2)))

        axFit.set_ylabel(r'$\Delta$ f / Hz')
        axFit.legend(bbox_to_anchor=(1, 1))
        axFit.grid()

        axResiduals.plot(self.bias, self.fitInfo.residual, '.', color='gray')
        axResiduals.set_ylabel('residuals / Hz')
        axResiduals.set_xlabel('bias / V')
        axResiduals.grid()

        plt.tight_layout()
        plt.subplots_adjust(wspace=0, hspace=0)

        return fig, axFit, axResiduals



