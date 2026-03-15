import React, { useState, useEffect, useRef, useCallback } from 'react';
import { createPortal } from 'react-dom';
import axios from 'axios';
import { Search, MapPin, TrendingUp, BarChart2, Award, Info, Activity, HelpCircle, Loader2 } from 'lucide-react';
import {
  ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, Radar,
  ScatterChart, Scatter, XAxis, YAxis, Cell,
  ReferenceLine, ReferenceArea, Tooltip,
} from 'recharts';
import { SpeedInsights } from "@vercel/speed-insights/react"

// 사분면 메타 정보
const QUADRANT_META = {
  'Q1_검증시장공백':   { color: '#10b981', short: 'Q1', label: '수요가 입증된 안전 진입지', desc: '매출↑ · 경쟁↓' },
  'Q2_잠재수요미실현': { color: '#6366f1', short: 'Q2', label: '선점 가능한 블루오션',     desc: '잠재수요↑ · 경쟁↓' },
  'Q4_레드오션':      { color: '#f43f5e', short: 'Q4', label: '이미 포화된 시장',         desc: '매출↑ · 경쟁↑' },
  'Q3_저성과포화':    { color: '#94a3b8', short: 'Q3', label: '진입 비추천',              desc: '매출↓ · 경쟁↑' },
};

const QUADRANT_ORDER = ['Q1_검증시장공백', 'Q2_잠재수요미실현', 'Q4_레드오션', 'Q3_저성과포화'];

const getQuadrantColor = (quad) => QUADRANT_META[quad]?.color ?? '#475569';

// 블루오션 여부 hover 설명 컴포넌트 — Portal로 렌더링해 부모 overflow에 잘리지 않음
const BlueOceanTooltip = () => {
  const [show, setShow] = useState(false);
  const [pos, setPos] = useState({ top: 0, left: 0 });
  const btnRef = useRef(null);

  const calcPos = () => {
    if (!btnRef.current) return;
    const rect = btnRef.current.getBoundingClientRect();
    const TW = 272; // tooltip width (w-68 ≈ 272px)
    const TH = 160; // approx height
    let left = rect.left - TW / 2 + rect.width / 2;
    if (left < 8) left = 8;
    if (left + TW > window.innerWidth - 8) left = window.innerWidth - TW - 8;
    let top = rect.top - TH - 8;
    if (top < 8) top = rect.bottom + 8;
    setPos({ top, left });
  };

  useEffect(() => {
    const hide = () => setShow(false);
    document.addEventListener('scroll', hide, true);
    return () => document.removeEventListener('scroll', hide, true);
  }, []);

  return (
    <div className="flex items-center">
      <button
        ref={btnRef}
        onMouseEnter={() => { calcPos(); setShow(true); }}
        onMouseLeave={() => setShow(false)}
        onClick={() => { if (!show) { calcPos(); setShow(true); } else setShow(false); }}
        className="text-blue-200/50 hover:text-blue-200 transition-colors"
      >
        <HelpCircle size={14} />
      </button>
      {show && createPortal(
        <div
          style={{ position: 'fixed', top: pos.top, left: pos.left, zIndex: 9999, width: 272 }}
          className="bg-slate-900 border border-slate-600 rounded-xl p-3 text-xs text-slate-300 shadow-2xl"
          onMouseEnter={() => setShow(true)}
          onMouseLeave={() => setShow(false)}
        >
          <div className="font-bold text-white mb-2">블루오션 분류 기준</div>
          <div className="space-y-1.5">
            <div className="flex items-start gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 mt-1 flex-shrink-0" />
              <span><b className="text-emerald-400">블루오션</b>: Q1(수요가 입증된 안전 진입지) 또는 Q2(선점 가능한 블루오션) 상권</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="w-2 h-2 rounded-full bg-slate-400 mt-1 flex-shrink-0" />
              <span><b className="text-slate-400">일반</b>: Q3(진입 비추천) 또는 Q4(이미 포화된 시장) 상권</span>
            </div>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-700 text-slate-500">
            현재 분석 대상: 1,036개 서울 상권
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

const App = () => {
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverStatus, setServerStatus] = useState('checking');
  const [scatterData, setScatterData] = useState(null);
  const [retrying, setRetrying] = useState(false);
  const [retryIn, setRetryIn] = useState(0);
  const retryTimerRef = useRef(null);
  const pendingAddressRef = useRef('');

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    const checkServer = async () => {
      try { await axios.get(apiUrl, { timeout: 5000 }); setServerStatus('online'); }
      catch { setServerStatus('offline'); }
    };
    checkServer();
  }, [apiUrl]);

  useEffect(() => {
    axios.get(`${apiUrl}/scatter`).then(r => setScatterData(r.data)).catch(() => {});
  }, [apiUrl]);

  // 타이머 정리
  useEffect(() => () => clearInterval(retryTimerRef.current), []);

  const cancelRetry = useCallback(() => {
    clearInterval(retryTimerRef.current);
    setRetrying(false);
    setRetryIn(0);
    setLoading(false);
  }, []);

  const doSearch = useCallback(async (addr) => {
    setLoading(true); setResult(null); setError(null);
    const trimmed = addr.trim();
    const isRank = /^\d+$/.test(trimmed);
    const url = isRank
      ? `${apiUrl}/rank/${trimmed}`
      : `${apiUrl}/search?address=${encodeURIComponent(addr)}`;
    try {
      const response = await axios.get(url);
      setRetrying(false);
      clearInterval(retryTimerRef.current);
      setResult(response.data);
      setServerStatus('online');
      if (!scatterData) {
        axios.get(`${apiUrl}/scatter`).then(r => setScatterData(r.data)).catch(() => {});
      }
    } catch (err) {
      const isNetworkError = !err.response;
      if (isNetworkError) {
        // 콜드 스타트: 20초 카운트다운 후 자동 재시도
        setRetrying(true);
        setServerStatus('offline');
        let countdown = 20;
        setRetryIn(countdown);
        clearInterval(retryTimerRef.current);
        retryTimerRef.current = setInterval(() => {
          countdown -= 1;
          setRetryIn(countdown);
          if (countdown <= 0) {
            clearInterval(retryTimerRef.current);
            doSearch(pendingAddressRef.current);
          }
        }, 1000);
      } else {
        setRetrying(false);
        const msg = err.response?.data?.detail;
        setError(msg || '분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.');
      }
    } finally { setLoading(false); }
  }, [apiUrl, scatterData]);

  const handleSearch = useCallback(async (e) => {
    e.preventDefault();
    if (!address) return;
    pendingAddressRef.current = address;
    cancelRetry();
    doSearch(address);
  }, [address, doSearch, cancelRetry]);

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-100 p-4 md:p-12 font-sans selection:bg-blue-500/30">
      <SpeedInsights />

      <div className="max-w-6xl mx-auto flex justify-end mb-4">
        <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border ${
          serverStatus === 'online'  ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' :
          serverStatus === 'offline' ? 'bg-amber-500/10  border-amber-500/50  text-amber-400'   :
                                       'bg-slate-700/50  border-slate-600     text-slate-400'
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
        <section className="bg-slate-800/50 backdrop-blur-xl p-2 rounded-2xl border border-slate-700 shadow-2xl mb-12">
          <form onSubmit={handleSearch} className="flex flex-col md:flex-row gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500" size={22} />
              <input
                type="text" value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="서울 주소 입력 (구 단위 포함) 또는 순위 번호 (예: 5)"
                className="w-full bg-transparent border-none rounded-xl py-5 pl-14 pr-4 text-lg focus:outline-none focus:ring-0 placeholder:text-slate-600 font-medium"
              />
            </div>
            <button type="submit" disabled={loading || retrying}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white px-10 py-4 md:py-0 rounded-xl font-bold text-lg transition-all shadow-lg shadow-blue-900/20 active:scale-95">
              {loading ? '데이터 분석 중...' : retrying ? '서버 시작 중...' : '분석하기'}
            </button>
          </form>
        </section>

        {retrying && (
          <div className="bg-amber-900/20 border border-amber-500/50 text-amber-200 p-5 rounded-2xl mb-8 flex items-center gap-4">
            <Loader2 size={22} className="animate-spin text-amber-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="font-medium">분석 서버를 시작하는 중입니다...</p>
              <p className="text-xs mt-0.5 text-amber-400/70">{retryIn}초 후 자동 재시도 · 처음 요청 시 최대 40초 소요</p>
            </div>
            <button onClick={cancelRetry} className="text-amber-400/60 hover:text-amber-400 text-xs underline flex-shrink-0">취소</button>
          </div>
        )}

        {error && (
          <div className="bg-red-900/20 border border-red-500/50 text-red-200 p-5 rounded-2xl mb-8 flex items-center gap-4">
            <div className="bg-red-500 p-1 rounded-full"><Info size={20} className="text-white" /></div>
            <span className="font-medium">{error}</span>
          </div>
        )}

        {result && (
          <div className="space-y-8 animate-in fade-in zoom-in-95 duration-500">
            {/* 상단 카드 그리드 */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Main Ranking Card */}
              <div className={`lg:col-span-4 p-10 rounded-[2.5rem] shadow-2xl flex flex-col items-center justify-center text-center relative overflow-hidden group bg-gradient-to-br ${result.is_blue_ocean ? 'from-sky-400 to-cyan-600' : 'from-rose-600 to-red-800'}`}>
                <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16 blur-3xl group-hover:bg-white/20 transition-all duration-700" />
                <Award size={80} className="mb-6 text-yellow-300" />
                <h2 className="text-xl font-bold text-blue-100 mb-2">블루오션 입지 순위</h2>

                {result.ranking != null ? (
                  <>
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="text-8xl font-black tracking-tighter text-white">{result.ranking}</span>
                      <span className="text-3xl font-bold text-blue-200">위</span>
                    </div>
                    <div className="bg-black/20 backdrop-blur-md px-6 py-2 rounded-full text-sm font-black text-white border border-white/10 mb-10">
                      전체 {(result.total_ranked ?? 1036).toLocaleString()}개 상권 중
                    </div>
                  </>
                ) : (
                  <div className="mb-10 text-center">
                    {result.quadrant && (result.quadrant === 'Q3_저성과포화' || result.quadrant === 'Q4_레드오션') ? (
                      <>
                        <div className="text-3xl font-black text-white/60 mb-2">순위 미제공</div>
                        <div className="bg-black/20 px-4 py-2 rounded-full text-sm text-white/70 border border-white/10">
                          {QUADRANT_META[result.quadrant]?.label} 상권
                        </div>
                      </>
                    ) : (
                      <>
                        <div className="text-3xl font-black text-white/60 mb-2">미분석 상권</div>
                        <div className="bg-black/20 px-4 py-2 rounded-full text-sm text-white/70 border border-white/10">
                          분석 대상 외 상권
                        </div>
                      </>
                    )}
                  </div>
                )}

                <div className="w-full space-y-4 pt-6 border-t border-white/20">
                  {/* 사분면 분류 — 4개 전부 표시 */}
                  <div>
                    <div className="text-blue-100/70 font-medium text-sm mb-2 text-left">사분면 분류</div>
                    <div className="grid grid-cols-2 gap-1.5">
                      {QUADRANT_ORDER.map(key => {
                        const { color, short, label } = QUADRANT_META[key];
                        const isThis = result.quadrant === key;
                        return (
                          <div key={key}
                            className={`px-2 py-1.5 rounded-lg text-xs text-left border transition-all ${isThis ? 'border-white/50 scale-105' : 'border-white/10 opacity-40'}`}
                            style={{ backgroundColor: `${color}25`, borderColor: isThis ? color : undefined }}>
                            <div className="font-black" style={{ color: isThis ? color : '#fff' }}>{short}</div>
                            <div className="text-white/80 leading-tight text-[10px]">{label}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* 블루오션 여부 */}
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-1.5">
                      <span className="text-white/70 font-medium">블루오션</span>
                      <BlueOceanTooltip is_blue_ocean={result.is_blue_ocean} />
                    </div>
                    <div className={`px-4 py-1 rounded-lg font-black text-lg ${result.is_blue_ocean ? 'bg-white/20 text-white' : 'bg-white/10 text-white/60'}`}>
                      {result.is_blue_ocean ? 'O' : 'X'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Metrics Dashboard */}
              <div className="lg:col-span-8 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Sales Scale */}
                <div className="bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group hover:border-emerald-500/50 transition-all duration-300">
                  <div className="w-14 h-14 bg-emerald-500/10 rounded-2xl flex items-center justify-center text-emerald-400 mb-6 group-hover:scale-110 transition-transform">
                    <TrendingUp size={32} />
                  </div>
                  <h3 className="text-slate-400 font-bold mb-2">동종업계 월매출 규모</h3>
                  {result.sales_per_store != null ? (
                    <>
                      <div className="text-4xl font-black text-white mb-1">
                        {(result.sales_per_store / 10000).toLocaleString(undefined, {maximumFractionDigits: 0})}
                        <span className="text-lg font-bold text-slate-500"> 만원/월</span>
                      </div>
                      <p className="text-slate-500 text-xs">점포당 월평균 ({result.cafe_store_count ?? '?'}개 점포 기준)</p>
                    </>
                  ) : (
                    <div className="text-2xl font-black text-slate-500">분석 데이터 없음</div>
                  )}
                </div>

                {/* District Name */}
                <div className="bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group hover:border-blue-500/50 transition-all duration-300">
                  <div className="w-14 h-14 bg-blue-500/10 rounded-2xl flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform">
                    <MapPin size={32} />
                  </div>
                  <h3 className="text-slate-400 font-bold mb-2">매핑 상권명</h3>
                  <div className="text-3xl font-black text-white mb-2 truncate max-w-full">{result.district_name}</div>
                  <p className="text-slate-500 text-sm font-medium">검색 주소와 가장 인접한 분석 상권</p>
                </div>

                {/* Tea shop penetration rate */}
                {(() => {
                  const teaCnt  = result.tea_shop_count ?? 0;
                  const cafeCnt = result.cafe_store_count ?? 1;
                  const ratio   = cafeCnt > 0 ? Math.round((teaCnt / cafeCnt) * 100) : 0;
                  // 낮을수록 찻집이 없어 블루오션
                  const color = ratio === 0 ? 'emerald' : ratio < 15 ? 'amber' : 'rose';
                  const colorMap = {
                    emerald: { border: 'hover:border-emerald-500/50', bg: 'bg-emerald-500/10', text: 'text-emerald-400', val: 'text-emerald-300' },
                    amber:   { border: 'hover:border-amber-500/50',   bg: 'bg-amber-500/10',   text: 'text-amber-400',   val: 'text-amber-300' },
                    rose:    { border: 'hover:border-rose-500/50',    bg: 'bg-rose-500/10',    text: 'text-rose-400',    val: 'text-rose-300' },
                  };
                  const c = colorMap[color];
                  return (
                    <div className={`bg-slate-800/40 border border-slate-700 p-8 rounded-3xl flex flex-col items-center text-center group ${c.border} transition-all duration-300`}>
                      <div className={`w-14 h-14 ${c.bg} rounded-2xl flex items-center justify-center ${c.text} mb-6 group-hover:scale-110 transition-transform`}>
                        <BarChart2 size={32} />
                      </div>
                      <h3 className="text-slate-400 font-bold mb-2">찻집 시장 침투율</h3>
                      <div className={`text-4xl font-black ${c.val} mb-1`}>
                        {ratio}<span className="text-2xl font-bold text-slate-500">%</span>
                      </div>
                      <div className="flex items-center gap-2 mb-2">
                        <div className="bg-slate-700/50 rounded-lg px-3 py-1 text-xs text-slate-400">
                          카페 <span className="text-white font-bold">{cafeCnt}개</span>
                        </div>
                        <span className="text-slate-600 text-xs">vs</span>
                        {/* 찻집 N개 — 이름 있으면 hover tooltip */}
                        {result.tea_shop_names?.length > 0 ? (
                          <div className="relative group/teashop">
                            <div className="bg-slate-700/50 rounded-lg px-3 py-1 text-xs text-slate-400 cursor-default flex items-center gap-1">
                              찻집 <span className="font-bold text-white">{teaCnt}개</span>
                              <span className="text-slate-600 text-[10px]">▴</span>
                            </div>
                            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 z-50 hidden group-hover/teashop:block bg-slate-900 border border-slate-600 rounded-xl p-3 shadow-2xl min-w-[140px] text-left whitespace-nowrap">
                              <div className="text-slate-500 text-xs mb-1.5">이 상권의 찻집</div>
                              {result.tea_shop_names.map((name, i) => (
                                <div key={i} className="text-white text-xs py-0.5">· {name}</div>
                              ))}
                            </div>
                          </div>
                        ) : (
                          <div className="bg-slate-700/50 rounded-lg px-3 py-1 text-xs text-slate-400">
                            찻집 <span className="font-bold text-emerald-400">{teaCnt}개</span>
                          </div>
                        )}
                      </div>
                      <p className="text-slate-500 text-xs">
                        공급 공백 지수 <span className="text-slate-400 font-medium">{result.supply_shortage ?? 0}%</span>
                      </p>
                    </div>
                  );
                })()}

                {/* Demand Factors Radar */}
                <div className="bg-slate-800/40 border border-slate-700 p-6 rounded-3xl flex flex-col group hover:border-slate-500 transition-all duration-300">
                  <h3 className="font-bold text-slate-400 mb-4 flex items-center justify-center gap-2">
                    <Info size={18} />
                    수요 요인 지수 <span className="text-xs font-normal text-slate-600">(서울 내 백분위)</span>
                  </h3>
                  <div className="h-56 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart cx="50%" cy="50%" outerRadius="75%" data={result.demand_factors}>
                        <PolarGrid stroke="#334155" />
                        <PolarAngleAxis dataKey="subject" tick={{ fill: '#94a3b8', fontSize: 12, fontWeight: 700 }} />
                        <Radar name="상권 지수" dataKey="value" stroke="#6366f1" strokeWidth={3} fill="#6366f1" fillOpacity={0.3} />
                        <Tooltip
                          cursor={false}
                          content={({ active, payload }) => {
                            if (!active || !payload?.length) return null;
                            const item = payload[0]?.payload;
                            if (!item) return null;
                            return (
                              <div className="bg-slate-900 border border-indigo-500/50 rounded-xl p-3 shadow-2xl" style={{ maxWidth: 240 }}>
                                <div className="font-bold text-indigo-400 text-xs mb-1.5">{item.subject}</div>
                                {item.subject === '지하철' && item.detail && item.detail !== '-'
                                  ? item.detail.split(', ').map((s, i) => (
                                      <div key={i} className="text-white text-sm font-semibold leading-snug">{s}</div>
                                    ))
                                  : <div className="text-white text-sm font-semibold leading-snug">{item.detail ?? '-'}</div>
                                }
                                <div className="text-slate-500 text-xs mt-1.5">서울 내 {item.value}백분위</div>
                              </div>
                            );
                          }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </div>

            {/* 2D 매트릭스 */}
            {scatterData && (
              <div className="bg-slate-800/40 border border-slate-700 p-6 md:p-8 rounded-3xl">
                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4 mb-6">
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">블루오션 2D 매트릭스</h3>
                    <p className="text-slate-400 text-sm">
                      분석 상권 {scatterData.points.length}개 —{' '}
                      <span className="text-amber-400 font-bold">{result.district_name}</span> 강조 표시
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {QUADRANT_ORDER.map(key => {
                      const { color, label } = QUADRANT_META[key];
                      return (
                        <div key={key} className="flex items-center gap-1.5 text-xs text-slate-300">
                          <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
                          {label}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* 사분면 설명 카드 */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                  {QUADRANT_ORDER.map(key => {
                    const { color, label, desc } = QUADRANT_META[key];
                    const isTarget = result.quadrant === key;
                    return (
                      <div key={key}
                        className={`p-3 rounded-2xl border text-xs transition-all ${isTarget ? 'scale-105 shadow-lg' : 'opacity-60'}`}
                        style={{ backgroundColor: `${color}15`, borderColor: isTarget ? color : '#334155' }}>
                        <div className="font-bold mb-1" style={{ color }}>{label}</div>
                        <div className="text-slate-400 whitespace-pre-line leading-relaxed">{desc}</div>
                        {isTarget && <div className="mt-2 text-[11px] font-black" style={{ color }}>← 현재 상권</div>}
                      </div>
                    );
                  })}
                </div>

                {/* Scatter Chart */}
                <div className="h-80 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 10, right: 20, bottom: 20, left: 10 }}>
                      <ReferenceArea x1={scatterData.threshold_x} y1={0}  x2={1.06} y2={4}   fill="#10b981" fillOpacity={0.06} />
                      <ReferenceArea x1={scatterData.threshold_x} y1={-7} x2={1.06} y2={0}   fill="#6366f1" fillOpacity={0.06} />
                      <ReferenceArea x1={-0.05} y1={0}  x2={scatterData.threshold_x} y2={4}  fill="#f43f5e" fillOpacity={0.04} />
                      <ReferenceArea x1={-0.05} y1={-7} x2={scatterData.threshold_x} y2={0}  fill="#94a3b8" fillOpacity={0.04} />
                      <ReferenceLine y={0}                        stroke="#475569" strokeDasharray="5 3" strokeWidth={1.5} />
                      <ReferenceLine x={scatterData.threshold_x}  stroke="#475569" strokeDasharray="5 3" strokeWidth={1.5} />
                      <XAxis type="number" dataKey="x" name="공급부족 지수"
                        domain={[-0.05, 1.06]} tick={{ fill: '#64748b', fontSize: 11 }}
                        label={{ value: '← 찻집 있음 · 없음 →', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 11 }} />
                      <YAxis type="number" dataKey="y" name="수요 잔차"
                        domain={[-7, 4]} tick={{ fill: '#64748b', fontSize: 11 }}
                        label={{ value: '수요 잔차', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 11 }} />
                      <Tooltip cursor={false}
                        content={({ active, payload }) => {
                          if (!active || !payload?.length) return null;
                          const d = payload[0].payload;
                          const isT = d.상권_코드_명 === result.district_name;
                          return (
                            <div className={`px-3 py-2 rounded-xl text-xs border shadow-xl ${isT ? 'bg-amber-900/90 border-amber-500' : 'bg-slate-800/90 border-slate-600'}`}>
                              <div className="font-bold mb-1" style={{ color: isT ? '#f59e0b' : getQuadrantColor(d.사분면) }}>{d.상권_코드_명}</div>
                              <div className="text-slate-300">{QUADRANT_META[d.사분면]?.label ?? d.사분면}</div>
                              <div className="text-slate-400">잔차: {d.y?.toFixed(2)}</div>
                            </div>
                          );
                        }}
                      />
                      <Scatter data={scatterData.points} isAnimationActive={false}>
                        {scatterData.points.map((entry, i) => {
                          const isTarget = entry.상권_코드_명 === result.district_name;
                          return (
                            <Cell key={i}
                              fill={isTarget ? '#f59e0b' : getQuadrantColor(entry.사분면)}
                              fillOpacity={isTarget ? 1 : 0.18}
                              stroke={isTarget ? '#fff' : 'none'}
                              strokeWidth={isTarget ? 2 : 0}
                              r={isTarget ? 9 : 3}
                            />
                          );
                        })}
                      </Scatter>
                    </ScatterChart>
                  </ResponsiveContainer>
                </div>
                <p className="text-center text-slate-600 text-xs mt-3">
                  X축: 공급부족 지수 (우측=찻집 없음) · Y축: OOF 잔차 (위=수요 대비 매출 좋음)
                </p>
              </div>
            )}
          </div>
        )}

        {!result && !loading && (
          <div className="flex flex-col items-center justify-center py-16 select-none">
            <img
              src="/mint-tea.svg"
              alt="찻집 일러스트"
              className="w-64 h-64 opacity-70 mb-6"
              draggable="false"
            />
            <p className="text-lg font-semibold text-slate-500 mb-1">서울 찻집 블루오션 상권 찾기</p>
            <p className="text-sm text-slate-600">주소 또는 순위 번호를 입력하면 인접 상권을 분석해드려요.</p>
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
