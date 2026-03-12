import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, MapPin, TrendingUp, BarChart2, Award, Info, Activity } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar } from 'recharts';
import { SpeedInsights } from "@vercel/speed-insights/react"

const App = () => {
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking'); // checking, online, offline

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // 서버 상태 체크 (Render Cold Start 대응)
  useEffect(() => {
    const checkServer = async () => {
      try {
        await axios.get(apiUrl, { timeout: 5000 });
        setServerStatus('online');
      } catch (err) {
        setServerStatus('offline');
      }
    };
    checkServer();
  }, [apiUrl]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!address) return;
    
    setLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const response = await axios.get(`${apiUrl}/search?address=${encodeURIComponent(address)}`);
      setResult(response.data);
    } catch (err) {
      setError('상권 정보를 불러오는 데 실패했습니다. 서버가 깨어나는 중일 수 있으니 잠시 후 다시 시도해 주세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100 p-4 md:p-12 font-sans selection:bg-blue-500/30">
      <SpeedInsights />
      
      {/* Server Status Indicator */}
      <div className="max-w-6xl mx-auto flex justify-end mb-4">
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
          serverStatus === 'online' ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' : 
          serverStatus === 'offline' ? 'bg-amber-500/10 border-amber-500/50 text-amber-400' : 'bg-slate-700/50 border-slate-600 text-slate-400'
        }`}>
          <Activity size={14} className={serverStatus === 'checking' ? 'animate-pulse' : ''} />
          {serverStatus === 'online' ? '분석 서버 연결됨' : serverStatus === 'offline' ? '서버 깨우는 중...' : '서버 확인 중'}
        </div>
      </div>

      <header className="max-w-6xl mx-auto mb-12 text-center">
        <h1 className="text-5xl md:text-6xl font-black bg-gradient-to-r from-blue-400 via-indigo-400 to-emerald-400 bg-clip-text text-transparent mb-4 tracking-tight">
          BlueOcean Finder
        </h1>
        <p className="text-slate-400 text-lg md:text-xl font-medium">서울시 찻집 상권 블루오션 입지 분석 서비스</p>
      </header>

      <main className="max-w-6xl mx-auto">
        {/* Search Bar */}
        <section className="bg-slate-800/50 backdrop-blur-xl p-2 rounded-2xl border border-slate-700 shadow-2xl mb-12">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" size={22} />
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="분석하고 싶은 주소를 입력하세요 (구 단위 포함 권장)"
                className="w-full bg-transparent border-none rounded-xl py-5 pl-14 pr-4 text-lg focus:outline-none focus:ring-0 placeholder:text-slate-600 transition-all font-medium"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white px-10 py-4 md:py-0 rounded-xl font-bold text-lg transition-all shadow-lg shadow-blue-900/20 active:scale-95"
            >
              {loading ? '데이터 분석 중...' : '분석하기'}
            </button>
          </form>
        </section>

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 text-red-200 p-5 rounded-2xl mb-8 flex items-center gap-4 animate-in slide-in-from-top-4 duration-300">
            <div className="bg-red-500 p-1 rounded-full"><Info size={20} className="text-white" /></div>
            <span className="font-medium">{error}</span>
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 animate-in fade-in zoom-in-95 duration-500">
            {/* Main Ranking Card */}
            <div className="lg:col-span-4 bg-gradient-to-br from-indigo-600 to-blue-800 p-10 rounded-[2.5rem] shadow-2xl flex flex-col items-center justify-center text-center relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-white/20 transition-all duration-700"></div>
              <Award size={80} className="mb-6 text-yellow-300 drop-shadow-glow" />
              <h2 className="text-xl font-bold text-blue-100 mb-2">블루오션 입지 순위</h2>
              <div className="flex items-baseline gap-2 mb-4">
                <span className="text-8xl font-black tracking-tighter text-white">
                  {typeof result.ranking === 'number' ? result.ranking : result.ranking}
                </span>
                {typeof result.ranking === 'number' && <span className="text-3xl font-bold text-blue-200">위</span>}
              </div>
              <div className="bg-black/20 backdrop-blur-md px-6 py-2 rounded-full text-sm font-black text-white border border-white/10 mb-10">
                서울 1,139개 상권 중
              </div>
              
              <div className="w-full space-y-4 pt-6 border-t border-white/20">
                <div className="flex justify-between items-center">
                  <span className="text-blue-100/70 font-medium">사분면 분류</span>
                  <span className="font-black text-white text-lg">{result.quadrant || '일반 상권'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-blue-100/70 font-medium">블루오션 여부</span>
                  <div className={`flex items-center gap-2 px-3 py-1 rounded-lg font-black ${result.is_blue_ocean ? 'bg-emerald-400 text-emerald-950' : 'bg-white/10 text-white'}`}>
                    {result.is_blue_ocean ? '확인됨' : '일반'}
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Dashboard */}
            <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Sales Prediction */}
              <div className="bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group hover:border-emerald-500/50 transition-all duration-300">
                <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
                  <TrendingUp size={32} />
                </div>
                <h3 className="text-slate-400 font-bold mb-2">예상 매출액</h3>
                <div className="text-4xl font-black text-white mb-2">
                  {(result.sales_prediction / 10000).toLocaleString(undefined, {maximumFractionDigits: 0})} <span className="text-lg font-bold text-slate-500">만원</span>
                </div>
                <p className="text-slate-500 text-sm font-medium">상권 내 수요 지표 기반 월 예측치</p>
              </div>

              {/* District Name */}
              <div className="bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group hover:border-blue-500/50 transition-all duration-300">
                <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
                  <MapPin size={32} />
                </div>
                <h3 className="text-slate-400 font-bold mb-2">매핑 상권명</h3>
                <div className="text-3xl font-black text-white mb-2 truncate max-w-full">
                  {result.district_name}
                </div>
                <p className="text-slate-500 text-sm font-medium">검색 주소와 가장 인접한 상권</p>
              </div>

              {/* Tea Shop Count */}
              <div className="bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group hover:border-amber-500/50 transition-all duration-300">
                <div className="w-14 h-14 bg-amber-500/10 rounded-2xl flex items-center justify-center text-amber-400 mb-6 group-hover:scale-110 transition-transform">
                  <BarChart2 size={32} />
                </div>
                <h3 className="text-slate-400 font-bold mb-2">실제 찻집 수</h3>
                <div className="text-4xl font-black text-white mb-2">
                  {result.tea_shop_count || 0} <span className="text-lg font-bold text-slate-500">개</span>
                </div>
                <p className="text-slate-500 text-sm font-medium">현재 영업 중인 경쟁 점포 수</p>
              </div>

              {/* Demand Factors Chart */}
              <div className="bg-slate-800/40 border border-slate-700 p-6 rounded-3xl flex flex-col group hover:border-slate-500 transition-all duration-300">
                <h3 className="font-bold text-slate-400 mb-4 flex items-center justify-center gap-2">
                  <Info size={18} />
                  수요 요인 지수
                </h3>
                <div className="h-56 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="75%" data={result.demand_factors}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 700 }} />
                      <Radar
                        name="상권 지수"
                        dataKey="value"
                        stroke="#6366f1"
                        strokeWidth={3}
                        fill="#6366f1"
                        fillOpacity={0.3}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center py-32 text-slate-700 animate-pulse">
            <div className="w-32 h-32 bg-slate-800/50 rounded-full flex items-center justify-center mb-6">
              <MapPin size={64} className="opacity-30" />
            </div>
            <p className="text-xl font-bold opacity-30">분석을 위해 주소를 입력해 주세요.</p>
          </div>
        )}
      </main>
      
      <footer className="max-w-6xl mx-auto mt-20 pt-8 border-t border-slate-800 text-center text-slate-600 text-sm">
        &copy; 2026 BlueOcean Finder. 서울시 상권 데이터를 기반으로 분석합니다.
      </footer>
    </div>
  );
};

export default App;
