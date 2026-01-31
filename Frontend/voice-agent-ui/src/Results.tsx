import React from 'react';

interface ResultsProps {
  data: {
    type: 'orders' | 'products' | null;
    items: any[];
  };
}

const Results: React.FC<ResultsProps> = ({ data }) => {
  if (!data.type) return (
    <div className="h-full flex items-center justify-center text-slate-500 italic font-mono">
      Awaiting Data Query...
    </div>
  );
const getStatusStep = (status: string) => {
  const steps: Record<string, number> = {
    'Placed': 0,
    'Shipped': 1,
    'Out for Delivery': 2,
    'Delivered': 3
  };
  return steps[status] ?? 0;
};

  return (
    <div className="h-full p-4 space-y-4 overflow-y-auto custom-scrollbar">
      <h2 className="text-cyan-400 font-bold tracking-tighter text-xl border-b border-slate-700 pb-2">
        {data.type === 'orders' ? '📦 ORDER HISTORY' : '🛍️ CATALOG MATCHES'}
      </h2>

      {data.items.map((order, idx) => (
  <div key={idx} className="bg-slate-800/40 border border-slate-700/50 p-4 rounded-xl mb-4 group hover:border-cyan-500/30 transition-all">
    
    {/* HEADER: ID and DATE */}
    <div className="flex justify-between items-center mb-3">
      <div>
        <span className="text-[10px] text-slate-500 block uppercase tracking-widest font-bold">Ref Number</span>
        <span className="text-cyan-400 font-mono text-sm">{order.order_id}</span>
      </div>
      {/* Inside your order mapping loop in Results.tsx */}
<div className="text-right">
  <span className="text-[10px] text-slate-500 block uppercase tracking-widest font-bold">
    Processed
  </span>
  <span className="text-slate-300 font-mono text-xs">
    {/* Option A: Simple split (Fastest) */}
    {order.order_date.split('T')[0]}

    {/* OR Option B: Format by locale (e.g., 12/12/2025) */}
    {/* {new Date(order.order_date).toLocaleDateString()} */}
  </span>
</div>
    </div>

    {/* PRODUCT LIST: Mapping through the products array */}
    <div className="space-y-2 mb-4 border-l-2 border-slate-700 pl-3">
      {order.products.map((p: any, pIdx: number) => (
        <div key={pIdx} className="flex flex-col">
          <span className="text-[10px] text-slate-500 uppercase">Item</span>
          <span className="text-slate-200 text-sm font-medium">{p.product_name}</span>
          <span className="text-[9px] text-cyan-600 font-mono">{p.product_id}</span>
        </div>
      ))}
    </div>

    {/* Inside your order mapping loop */}
<div className="mt-4 pt-4 border-t border-slate-700/50">
  {order.order_status === 'Delivered' ? (
  /* DELIVERED STATE - Green Box */
  <div className="bg-emerald-500/10 border border-emerald-500/50 p-2 rounded text-center">
    <span className="text-emerald-500 font-bold text-xs uppercase tracking-[0.2em]">
      Order Delivered
    </span>
  </div>
) : order.order_status === 'Cancelled' ? (
  /* CANCELLED STATE - Red Box */
  <div className="bg-red-500/10 border border-red-500/50 p-2 rounded text-center">
    <span className="text-red-500 font-bold text-xs uppercase tracking-[0.2em]">
      Order Cancelled
    </span>
  </div>
) : (
  /* PROGRESS SLIDER STATE - For Placed, Shipped, Out for Delivery */
  <div className="space-y-3">
    {/* The Track */}
    <div className="relative h-1 w-full bg-slate-800 rounded-full overflow-hidden">
      {/* The Fill */}
      <div 
        className="absolute h-full bg-cyan-500 shadow-[0_0_8px_#22d3ee] transition-all duration-1000"
        style={{ width: `${(getStatusStep(order.order_status) / 3) * 100 + 5}%` }}
      ></div>
    </div>

    {/* The Labels */}
    <div className="flex justify-between items-start text-[8px] font-mono tracking-tighter uppercase">
      <div className={getStatusStep(order.order_status) >= 0 ? 'text-cyan-400' : 'text-slate-600'}>Placed</div>
      <div className={getStatusStep(order.order_status) >= 1 ? 'text-cyan-400' : 'text-slate-600'}>Shipped</div>
      <div className={getStatusStep(order.order_status) >= 2 ? 'text-cyan-400' : 'text-slate-600'}>Out for Delivery</div>
      <div className="text-slate-600">Delivered</div>
    </div>
  </div>
)}
</div>
  </div>
))}
    </div>
  );
};

export default Results;