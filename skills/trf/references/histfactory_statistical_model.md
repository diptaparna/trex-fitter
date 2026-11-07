# Mathematical Formulation of the HistFactory / xRooFit Statistical Model in TRExFitter

## 1. Binned Profile Likelihood Function

In `TRExFitter`, the statistical model is constructed via `HistFactory` (and evaluated via `RooFit` / `xRooFit`) as a product of Poisson probabilities across all analysis regions (channels) $c \in \text{Regions}$ and bins $i \in \{1, \dots, N_c\}$, multiplied by auxiliary constraint terms for nuisance parameters (NPs):

$$\mathcal{L}(\boldsymbol{\mu}, \boldsymbol{\theta}, \boldsymbol{\gamma} \mid \mathbf{n}, \mathbf{a}, \mathbf{m}) = \prod_{c \in \text{Regions}} \prod_{i=1}^{N_c} \text{Pois}\!\left(n_{ci} \,\middle|\, \nu_{ci}(\boldsymbol{\mu}, \boldsymbol{\theta}, \boldsymbol{\gamma})\right) \times \prod_{k \in \text{Syst}} f_k(a_k \mid \theta_k) \times \prod_{(c,i) \in \Gamma} g_{ci}(m_{ci} \mid \gamma_{ci})$$

where:
- $n_{ci}$ is the observed data (or Asimov/pseudodata) event count in bin $i$ of channel $c$.
- $\nu_{ci}(\boldsymbol{\mu}, \boldsymbol{\theta}, \boldsymbol{\gamma})$ is the expected event yield in bin $i$ of channel $c$:
  $$\nu_{ci}(\boldsymbol{\mu}, \boldsymbol{\theta}, \boldsymbol{\gamma}) = \gamma_{ci} \sum_{s \in \text{Samples}} \left[ \prod_{p \in \mathcal{N}_{cs}} \mu_p \right] \left[ \prod_{r \in \mathcal{S}_{csi}} \kappa_{ri} \right] \eta_{cs}(\boldsymbol{\theta}) \, \sigma_{csi}(\boldsymbol{\theta}) \, \nu_{csi}^0$$
- $\nu_{csi}^0$ is the nominal predicted yield of sample $s$ in channel $c$, bin $i$.
- $\mu_p$ are unconstrained normalization factors (`NormFactor`, including the Parameters of Interest, `POI`, and free-floating background normalizations), and $\kappa_{ri}$ are bin-by-bin unconstrained `ShapeFactor` parameters.
- $\boldsymbol{\theta} = (\theta_1, \dots, \theta_K)$ are the nuisance parameters (`alpha_<SystName>` in `RooFit`) parameterizing systematic uncertainties, with nominal global observables $a_k = 0$ and unit Gaussian constraints:
  $$f_k(a_k \mid \theta_k) = \frac{1}{\sqrt{2\pi}} \exp\!\left(-\frac{(a_k - \theta_k)^2}{2}\right)$$
  such that $\theta_k = 0$ corresponds to the nominal prediction and $\theta_k = \pm 1$ corresponds to the $\pm 1\sigma$ pre-fit systematic variation.
- $\gamma_{ci}$ (`gamma_stat_<Region>_bin_<i>` in `RooFit`) are the Barlow-Beeston "lite" Monte Carlo statistical uncertainty parameters, constrained by either a Poisson term (`MCstatConstraint: POISSON`, default) with effective unweighted MC count $m_{ci} = (\nu_{ci}^{\text{MC}} / \delta\nu_{ci}^{\text{MC}})^2$:
  $$g_{ci}(m_{ci} \mid \gamma_{ci}) = \frac{(\gamma_{ci} m_{ci})^{m_{ci}} e^{-\gamma_{ci} m_{ci}}}{\Gamma(m_{ci} + 1)}$$
  or a Gaussian constraint (`MCstatConstraint: GAUSSIAN`). When `SeparateGammas: TRUE` is enabled on a sample $s$, per-sample bin-by-bin parameters (`ShapeSys`) are introduced instead of merging that sample into the shared bin $\gamma_{ci}$.

---

## 2. Normalization and Shape Modifiers (`OverallSys` vs. `HistoSys`)

When a `Systematic` of `Type: HISTO` is processed in `TRExFitter`, its up/down template histograms $\nu_{csi}^{\pm}$ are decomposed into two distinct `HistFactory` components controlled by the **same** nuisance parameter $\theta_k$ (unless `Decorrelate: SHAPEACC` is specified):

1. **Overall Normalization Component (`OverallSys`, factor $\eta_{cs}(\theta_k)$)**:
   Let $I_{cs}^0 = \sum_i \nu_{csi}^0$ and $I_{cs}^{\pm} = \sum_i \nu_{csi}^{\pm}$. The relative yield variations are $\epsilon_{cs}^{\pm} = I_{cs}^{\pm} / I_{cs}^0$.
2. **Normalized Shape Component (`HistoSys`, template $\sigma_{csi}(\theta_k)$)**:
   The up/down templates are normalized to the nominal integral $I_{cs}^0$ in that region:
   $$\hat{\nu}_{csi}^{\pm} = \nu_{csi}^{\pm} \times \frac{I_{cs}^0}{I_{cs}^{\pm}}$$
   so that $\hat{\nu}_{csi}^{\pm}$ captures purely the relative migration of events across bins within region $c$.

### Interpolation Codes (`IntCodeOverall` and `IntCodeShape`)
By default (`IntCodeOverall: 4`, `IntCodeShape: 4` in `TRExFitter`), `HistFactory` uses **Code 4** (6th-order polynomial interpolation for $|\theta| < 1$ with continuous 1st and 2nd derivatives at $\theta = \pm 1$, stitched to exponential extrapolation for `OverallSys` and linear extrapolation for `HistoSys` at $|\theta| \ge 1$). This guarantees that:
- $\eta_{cs}(\theta)$ is strictly positive for all $\theta \in (-\infty, +\infty)$ (preventing negative yields from large normalization pulls), and
- $\partial \ln \mathcal{L} / \partial \theta$ and $\partial^2 \ln \mathcal{L} / \partial \theta^2$ are continuous across $\theta = 0$ and $\theta = \pm 1$, which is critical for `Minuit2` Hessian (`HESSE`) and `MIGRAD` convergence, especially when asymmetric up/down variations meet at $\theta = 0$.

---

## 3. Profile Likelihood Ratio and Test Statistics

Given a Parameter of Interest $\mu$ and nuisance parameters $\boldsymbol{\Theta} = (\boldsymbol{\theta}, \boldsymbol{\gamma}, \boldsymbol{\mu}_{\text{bkg}})$, the profile likelihood ratio is:
$$\lambda(\mu) = \frac{\mathcal{L}(\mu, \hat{\hat{\boldsymbol{\Theta}}}(\mu))}{\mathcal{L}(\hat{\mu}, \hat{\boldsymbol{\Theta}})}$$
where $(\hat{\mu}, \hat{\boldsymbol{\Theta}})$ is the unconditional Maximum Likelihood Estimate (MLE) and $\hat{\hat{\boldsymbol{\Theta}}}(\mu)$ is the conditional MLE for fixed $\mu$.

- **Parameter Uncertainties (`HESSE` and `MINOS`)**:
  The negative log-likelihood curve is $-2\Delta\ln\mathcal{L}(\mu) = -2\ln\lambda(\mu)$. Under Wilks' theorem, the $68.3\%$ ($1\sigma$) and $95.4\%$ ($2\sigma$) confidence intervals for a single parameter correspond to $-2\Delta\ln\mathcal{L}(\mu) = 1.0$ and $4.0$, respectively.
- **Discovery Test Statistic $q_0$ (`s` step)**:
  Tests the background-only hypothesis ($\mu = 0$) against a positive signal ($\mu > 0$):
  $$q_0 = \begin{cases} -2\ln\lambda(0) & \text{if } \hat{\mu} \ge 0 \\ 0 & \text{if } \hat{\mu} < 0 \end{cases}$$
  In the asymptotic approximation (Cowan et al., *Eur. Phys. J. C* 71 (2011) 1554), the discovery significance in standard deviations is $Z_0 = \sqrt{q_0}$.
- **Exclusion Limit Test Statistic $\tilde{q}_\mu$ (`l` step)**:
  For 95% $\text{CL}_s$ upper limits on $\mu > 0$ where negative signal is unphysical ($\mu \ge 0$):
  $$\tilde{q}_\mu = \begin{cases} -2\ln\frac{\mathcal{L}(\mu, \hat{\hat{\boldsymbol{\Theta}}}(\mu))}{\mathcal{L}(0, \hat{\hat{\boldsymbol{\Theta}}}(0))} & \text{if } \hat{\mu} < 0 \\ -2\ln\frac{\mathcal{L}(\mu, \hat{\hat{\boldsymbol{\Theta}}}(\mu))}{\mathcal{L}(\hat{\mu}, \hat{\boldsymbol{\Theta}})} & \text{if } 0 \le \hat{\mu} \le \mu \\ 0 & \text{if } \hat{\mu} > \mu \end{cases}$$
  The upper limit $\mu_{\text{up}}^{95\%}$ is the value of $\mu$ for which $\text{CL}_s(\mu) = \frac{p_{\mu}}{1 - p_b} = 0.05$.

---

## 4. Pulls, Constraints, and Impact ($\Delta\hat{\mu}$)

For a Gaussian-constrained nuisance parameter $\theta_k$ with pre-fit prior $\theta_k^0 = 0 \pm 1$:
- **Pull**: $\hat{\theta}_k - \theta_k^0 = \hat{\theta}_k$ (measured in units of the pre-fit standard deviation $\sigma_{\text{pre}} = 1$). Note: this is the *post-fit shift normalized to the pre-fit uncertainty*, not the studentized residual $\hat{\theta}_k / \sqrt{1 - (\Delta\hat{\theta}_k)^2}$ (though both are discussed in ATLAS statistics literature).
- **Constraint (Post-fit Uncertainty)**: $\Delta\hat{\theta}_k = \sigma_{\text{post}}(\theta_k) / \sigma_{\text{pre}}(\theta_k)$.
  - $\Delta\hat{\theta}_k \approx 1.0$: Data in the fit regions do not constrain $\theta_k$ beyond its auxiliary prior.
  - $\Delta\hat{\theta}_k < 1.0$ (e.g., $0.4$): The fit model + data constrain the NP more tightly than its prior ("over-constrained").
  - $\Delta\hat{\theta}_k > 1.0$: Indicates non-Gaussian/asymmetric profile likelihood curvature near the minimum or a numerical issue in the `HESSE` covariance matrix ("under-constrained").
- **Ranking Impact on POI (`r` step)**:
  For each NP $\theta_k$, `TRExFitter` performs four conditional fits fixing $\theta_k$ to:
  - Pre-fit impact: $\theta_k = \hat{\theta}_k \pm 1$ (shifting by the pre-fit $\pm 1\sigma$ around the best-fit value), yielding $\Delta\hat{\mu}_{\text{pre}}^{\pm} = \hat{\hat{\mu}}(\hat{\theta}_k \pm 1) - \hat{\mu}$.
  - Post-fit impact: $\theta_k = \hat{\theta}_k \pm \Delta\hat{\theta}_k$ (shifting by the post-fit $\pm 1\sigma$ uncertainty around the best-fit value), yielding $\Delta\hat{\mu}_{\text{post}}^{\pm} = \hat{\hat{\mu}}(\hat{\theta}_k \pm \Delta\hat{\theta}_k) - \hat{\mu}$.
- **Grouped Impact (`i` step)**:
  For a subset of NPs $G \subset \boldsymbol{\Theta}$ defined by `SubCategory`, a conditional fit is performed with all $\theta_k \in G$ fixed to their unconditional MLEs $\hat{\theta}_k$, yielding conditional POI uncertainty $\sigma_{\mu \mid G\text{ fixed}}$. The grouped impact is obtained by quadrature subtraction:
  $$\Delta\mu_G = \sqrt{\sigma_{\mu,\text{nominal}}^2 - \sigma_{\mu \mid G\text{ fixed}}^2}$$
