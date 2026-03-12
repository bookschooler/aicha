import React, { useState } from 'react';
import axios from 'axios';
import { Search, MapPin, TrendingUp, BarChart2, Award, Info } from 'lucide-react';
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend } from 'recharts';

const App = () => {
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!address) return;
    
    setLoading(true);
    setResult(null);
    setError(null);
    
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.get(`${apiUrl}/search?address=${encodeURIComponent(address)}`);
      setResult(response.data);
    } catch (err) {
      setError('상권 정보를 불러오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Mock radar data for visual demo (based on PRD metrics)
  const radarData = [
    { subject: '집객시설', A: 85, fullMark: 100 },
    { subject: '직장인구', A: 70, fullMark: 100 },
    { subject: '소득금액', A: 90, fullMark: 100 },
    { subject: '가구수', A: 65, fullMark: 100 },
    { subject: '검색지수', A: 80, fullMark: 100 },
    { subject: '지하철', A: 95, fullMark: 100 },
  ];

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-4 md:p-8 font-sans">
      <header className="max-w-6xl mx-auto mb-10 text-center">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-emerald-400 bg-clip-text text-transparent mb-2">
          BlueOcean Finder
        </h1>
        <p className="text-slate-400">서울시 찻집 상권 블루오션 입지 분석 서비스</p>
      </header>

      <main className="max-w-6xl mx-auto">
        {/* Search Bar */}
        <section className="bg-slate-800 p-6 rounded-2xl shadow-xl mb-8">
          <form onSubmit={handleSearch} className="flex gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="분석하고 싶은 주소를 입력하세요 (예: 서울시 동대문구 이문동)"
                className="w-full bg-slate-900 border border-slate-700 rounded-xl py-4 pl-12 pr-4 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white px-8 rounded-xl font-bold transition-colors"
            >
              {loading ? '분석 중...' : '분석하기'}
            </button>
          </form>
        </section>

        {error && (
          <div className="bg-red-900/30 border border-red-500 text-red-200 p-4 rounded-xl mb-8 flex items-center gap-3">
            <Info size={20} />
            {error}
          </div>
        )}

        {result && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 animate-in fade-in duration-700">
            {/* Main Ranking Card */}
            <div className="md:col-span-1 bg-gradient-to-br from-blue-600 to-indigo-700 p-8 rounded-3xl shadow-2xl flex flex-col items-center justify-center text-center">
              <Award size={64} className="mb-4 text-yellow-300" />
              <h2 className="text-xl font-medium opacity-90 mb-2">블루오션 입지 순위</h2>
              <div className="text-7xl font-black mb-2">
                {result.ranking} <span className="text-2xl font-normal">위</span>
              </div>
              <p className="bg-white/20 px-4 py-1 rounded-full text-sm font-bold">
                서울 1,139개 상권 중
              </p>
              <div className="mt-8 w-full border-t border-white/20 pt-6">
                <div className="flex justify-between items-center mb-4">
                  <span className="opacity-80">사분면 분류</span>
                  <span className="font-bold">{result.quadrant}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="opacity-80">블루오션 여부</span>
                  <span className={`font-bold ${result.is_blue_ocean ? 'text-emerald-300' : 'text-slate-300'}`}>
                    {result.is_blue_ocean ? '확인됨' : '일반'}
                  </span>
                </div>
              </div>
            </div>

            {/* Metrics Dashboard */}
            <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 flex flex-col justify-between">
                <div className="flex items-center gap-3 text-emerald-400 mb-4">
                  <TrendingUp size={24} />
                  <h3 className="font-bold">예상 매출액</h3>
                </div>
                <div className="text-3xl font-bold">
                  {Math.round(result.sales_prediction / 10000).toLocaleString()} <span className="text-lg font-normal text-slate-400">만원/월</span>
                </div>
                <p className="text-slate-500 text-sm mt-2">상권 내 수요 지표 기반 예측치</p>
              </div>

              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 flex flex-col justify-between">
                <div className="flex items-center gap-3 text-blue-400 mb-4">
                  <MapPin size={24} />
                  <h3 className="font-bold">매핑 상권명</h3>
                </div>
                <div className="text-2xl font-bold">{result.district_name}</div>
                <p className="text-slate-500 text-sm mt-2">입력 주소 기준 가장 인접한 상권</p>
              </div>

              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 flex flex-col justify-between">
                <div className="flex items-center gap-3 text-amber-400 mb-4">
                  <BarChart2 size={24} />
                  <h3 className="font-bold">실제 찻집 수</h3>
                </div>
                <div className="text-3xl font-bold">
                  {result.tea_shop_count} <span className="text-lg font-normal text-slate-400">개</span>
                </div>
                <p className="text-slate-500 text-sm mt-2">현시점 등록된 경쟁 점포 수</p>
              </div>

              <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 group hover:bg-slate-750 transition-colors">
                <h3 className="font-bold mb-4 flex items-center gap-2">
                  <Info size={18} className="text-slate-400" />
                  수요 요인 분석
                </h3>
                <div className="h-48 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
                      <PolarGrid stroke="#334155" />
                      <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                      <Radar
                        name="상권 지수"
                        dataKey="A"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.5}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center py-20 text-slate-600">
            <MapPin size={64} className="mb-4 opacity-20" />
            <p className="text-lg">분석을 위해 상단의 검색창에 주소를 입력해 주세요.</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default App;
