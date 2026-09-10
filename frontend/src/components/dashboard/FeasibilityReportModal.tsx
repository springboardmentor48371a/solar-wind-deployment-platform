import { X, Printer, ShieldCheck, Sun, DollarSign, Leaf, MapPin } from 'lucide-react';

interface FeasibilityReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  site: {
    name: string;
    latitude: number;
    longitude: number;
    region: string;
    land_area: number;
    land_ownership: string;
    predicted_irradiance: number;
    predicted_wind_speed: number;
    predicted_temp: number;
    predicted_cloud_cover: number;
    predicted_elevation: number;
    predicted_slope: number;
    resource_score: number;
    geographic_score: number;
    infrastructure_score: number;
    environmental_score: number;
    economic_score: number;
    overall_score: number;
    suitability_class: string;
    created_at?: string;
  };
}

export const FeasibilityReportModal: React.FC<FeasibilityReportModalProps> = ({
  isOpen,
  onClose,
  site,
}) => {
  if (!isOpen) return null;

  // Engineering & Investment Estimates based on land area and resource yield
  const capacityMW = parseFloat(((site.land_area / 15000) * 1.0).toFixed(1)); // ~1 MW per 15,000 m2
  const annualMWhSolar = Math.round(capacityMW * site.predicted_irradiance * 365 * 0.78);
  const annualMWhWind = Math.round(capacityMW * Math.pow(site.predicted_wind_speed / 5.0, 3) * 2200);
  const totalAnnualMWh = site.predicted_irradiance >= 5.0 ? annualMWhSolar : (annualMWhSolar + annualMWhWind) / 2;
  const capexEstimatedCrores = (capacityMW * 4.2).toFixed(1); // approx ₹4.2 Cr per MW
  const paybackYears = (4.2 / (site.overall_score / 100 * 0.95)).toFixed(1);
  const co2OffsetTons = Math.round(totalAnnualMWh * 0.82); // ~0.82 tons CO2 per MWh in India

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4 sm:p-6 print:p-0 print:bg-white print:static">
      <div className="bg-slate-900 border border-slate-800 rounded-3xl max-w-4xl w-full shadow-2xl overflow-hidden print:border-none print:shadow-none print:text-black print:bg-white">
        
        {/* Modal Controls Bar (Hidden during printing) */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60 print:hidden">
          <div className="flex items-center space-x-2">
            <span className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400">
              <ShieldCheck className="w-5 h-5" />
            </span>
            <span className="text-sm font-bold text-white">Bankable Site Feasibility & Investment Report</span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={handlePrint}
              className="px-3.5 py-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-slate-950 font-bold text-xs rounded-xl flex items-center space-x-1.5 shadow transition-all"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Save PDF</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition-all"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Printable Report Body */}
        <div className="p-6 sm:p-8 space-y-6 print:p-6 print:space-y-4 text-slate-200 print:text-slate-900">
          
          {/* Executive Header */}
          <div className="border-b border-slate-800 pb-5 print:border-slate-300">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <span className="text-[11px] font-extrabold uppercase tracking-widest text-amber-400 print:text-amber-700 block mb-1">
                  Solar & Wind Deployment Intelligence Platform &bull; Technical Due Diligence
                </span>
                <h1 className="text-2xl sm:text-3xl font-black text-white print:text-slate-950">
                  {site.name}
                </h1>
                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 print:text-slate-600 mt-2 font-mono">
                  <span className="flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-amber-400" />
                    <span>Lat: {site.latitude}°, Lon: {site.longitude}°</span>
                  </span>
                  <span>&bull;</span>
                  <span>Region: {site.region}</span>
                  <span>&bull;</span>
                  <span>Land Scale: {site.land_area.toLocaleString()} m² ({(site.land_area * 0.000247105).toFixed(1)} Acres)</span>
                </div>
              </div>

              {/* Overall Grade Badge */}
              <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 text-center min-w-[140px] print:border-slate-400 print:bg-slate-100">
                <span className="text-xs uppercase font-extrabold text-slate-400 print:text-slate-700 block">Overall Score</span>
                <span className="text-3xl font-black text-amber-400 print:text-amber-600 block">{site.overall_score}%</span>
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-400 print:text-emerald-700">{site.suitability_class}</span>
              </div>
            </div>
          </div>

          {/* Section 1: Climatological & Environmental Intelligence */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 print:text-amber-700 mb-3 flex items-center space-x-1.5">
              <Sun className="w-4 h-4" />
              <span>1. AI Climatological & Terrain Intelligence (scikit-learn Regressor)</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Solar Irradiance (GHI)</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">🌞 {site.predicted_irradiance} kWh/m²/day</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Surface Wind Speed</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">💨 {site.predicted_wind_speed} m/s</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Ambient Temperature</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">🌡️ {site.predicted_temp} °C</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Cloud Fraction</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">☁️ {site.predicted_cloud_cover} %</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Digital Elevation (SRTM)</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">🏔️ {site.predicted_elevation} meters</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Derived Terrain Slope</span>
                <span className="text-sm font-bold text-white print:text-slate-900 mt-1 block">📐 {site.predicted_slope}° (Optimal)</span>
              </div>
            </div>
          </div>

          {/* Section 2: Weighted Decision Matrix Breakdown */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 print:text-amber-700 mb-3 flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4" />
              <span>2. Multi-Criteria Suitability Decision Matrix</span>
            </h3>

            <div className="bg-slate-950/60 p-4 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300 space-y-2.5 text-xs">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-300 print:text-slate-700">Resource Availability (35% Weight)</span>
                <span className="font-bold text-amber-400 print:text-amber-700">{site.resource_score} / 100</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-850 print:border-slate-200 pt-2">
                <span className="font-semibold text-slate-300 print:text-slate-700">Geographic & Slope Suitability (25% Weight)</span>
                <span className="font-bold text-amber-400 print:text-amber-700">{site.geographic_score} / 100</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-850 print:border-slate-200 pt-2">
                <span className="font-semibold text-slate-300 print:text-slate-700">Infrastructure & Grid Access (15% Weight)</span>
                <span className="font-bold text-amber-400 print:text-amber-700">{site.infrastructure_score} / 100</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-850 print:border-slate-200 pt-2">
                <span className="font-semibold text-slate-300 print:text-slate-700">Environmental Impact & Forests (15% Weight)</span>
                <span className="font-bold text-amber-400 print:text-amber-700">{site.environmental_score} / 100</span>
              </div>
              <div className="flex justify-between items-center border-t border-slate-850 print:border-slate-200 pt-2">
                <span className="font-semibold text-slate-300 print:text-slate-700">Economic & Land Tenure Feasibility (10% Weight)</span>
                <span className="font-bold text-amber-400 print:text-amber-700">{site.economic_score} / 100</span>
              </div>
            </div>
          </div>

          {/* Section 3: Financial & Investment Projections (Milestone 3 & 4) */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-amber-400 print:text-amber-700 mb-3 flex items-center space-x-1.5">
              <DollarSign className="w-4 h-4" />
              <span>3. Financial & Clean Energy Yield Projections</span>
            </h3>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Estimated Plant Cap</span>
                <span className="text-base font-black text-cyan-300 print:text-cyan-800 mt-1 block">⚡ ~{capacityMW} MW</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Annual Yield</span>
                <span className="text-base font-black text-amber-300 print:text-amber-800 mt-1 block">🔋 ~{totalAnnualMWh.toLocaleString()} MWh</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Estimated CapEx</span>
                <span className="text-base font-black text-emerald-300 print:text-emerald-800 mt-1 block">💰 ₹{capexEstimatedCrores} Cr</span>
              </div>
              <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800 print:bg-slate-50 print:border-slate-300">
                <span className="text-[10px] text-slate-400 uppercase font-bold block">Est. Payback</span>
                <span className="text-base font-black text-emerald-300 print:text-emerald-800 mt-1 block">⏱️ ~{paybackYears} Years</span>
              </div>
            </div>

            <div className="mt-3 p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-xs text-emerald-300 print:bg-emerald-50 print:border-emerald-300 print:text-emerald-900 flex items-center space-x-2">
              <Leaf className="w-4 h-4 flex-shrink-0 text-emerald-400" />
              <span><strong>ESG Impact:</strong> Developing this site offsets approximately <strong>{co2OffsetTons.toLocaleString()} Metric Tons of CO₂ annually</strong>, supporting India's 500 GW non-fossil capacity goals.</span>
            </div>
          </div>

          {/* Section 4: Final Recommendation Verdict */}
          <div className="p-4 rounded-xl bg-slate-950/90 border border-amber-500/30 print:bg-slate-100 print:border-slate-300 text-xs">
            <h4 className="font-extrabold text-amber-400 print:text-amber-800 uppercase tracking-wider mb-1">
              Final Recommendation Verdict
            </h4>
            <p className="text-slate-300 print:text-slate-700 leading-relaxed">
              Based on the combined <span className="font-bold text-white print:text-slate-900">Resource Availability ({site.resource_score}/100)</span> and <span className="font-bold text-white print:text-slate-900">Geographic Topography ({site.geographic_score}/100)</span>, this candidate site is classified as <span className="font-bold text-emerald-400 print:text-emerald-700">{site.suitability_class}</span> with a composite rating of <span className="font-bold text-amber-400 print:text-amber-700">{site.overall_score}%</span>. Proceeding to ground-truth EPC land survey and grid interconnection study is strongly recommended.
            </p>
          </div>

        </div>

      </div>
    </div>
  );
};
