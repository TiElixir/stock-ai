import React from 'react';

interface ResultsProps {
  data: {
    type: 'orders' | 'products' | null;
    items: any[];
  };
}

const Results: React.FC<ResultsProps> = ({ data }) => {
  if (!data || !data.items || data.items.length === 0) return null;

  // Helper for Order Progress Slider
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
    <div className="flex flex-col h-full text-slate-200">
      {/* HEADER */}
      <div className="p-6 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-cyan-400 font-bold tracking-tighter uppercase text-sm flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
              {data.type === 'products' ? 'Catalog Matches' : 'Order Intelligence'}
            </h2>
            <p className="text-[10px] text-slate-500 font-mono mt-1 uppercase tracking-widest">
              System found {data.items.length} relevant entries
            </p>
          </div>
        </div>
      </div>

      {/* CONTENT SCROLL AREA */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {data.items.map((item, idx) => (
          <div 
            key={idx} 
            className="bg-slate-900/40 border border-slate-800 p-5 rounded-2xl hover:border-cyan-500/30 transition-all group relative overflow-hidden"
          >
            {/* BACKGROUND DECOR */}
            <div className="absolute top-0 right-0 -mt-4 -mr-4 w-16 h-16 bg-cyan-500/5 blur-2xl rounded-full group-hover:bg-cyan-500/10 transition-colors" />

            {/* --- LAYOUT A: PRODUCT RESULTS --- */}
            {data.type === 'products' ? (
              <div className="relative z-10">
                <div className="flex justify-between items-start mb-2">
                  <span className="text-[9px] font-mono text-slate-600 uppercase tracking-widest">ID: {item.product_id}</span>
                  <span className="text-emerald-400 font-bold font-mono text-base">${item.price}</span>
                </div>
                <h3 className="text-slate-100 font-semibold text-lg mb-2 group-hover:text-cyan-400 transition-colors">
                  {item.product_name}
                </h3>
                <p className="text-slate-400 text-xs leading-relaxed line-clamp-3 mb-5 italic">
                  "{item.description}"
                </p>
                <button className="w-full py-2.5 bg-cyan-500/10 hover:bg-cyan-500 text-cyan-400 hover:text-white border border-cyan-500/20 rounded-xl text-[10px] font-bold uppercase tracking-widest transition-all">
                  Analyze Details
                </button>
              </div>
            ) : (
              /* --- LAYOUT B: ORDER RESULTS --- */
              <div className="relative z-10 space-y-4">
                {/* ID and Date Header */}
                <div className="flex justify-between items-center">
                  <div>
                    <span className="text-[9px] text-slate-500 block uppercase font-bold tracking-tighter">Reference</span>
                    <span className="text-cyan-400 font-mono text-sm">{item.order_id}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-[9px] text-slate-500 block uppercase font-bold tracking-tighter">Timestamp</span>
                    <span className="text-slate-300 font-mono text-xs">
                      {item.order_date ? item.order_date.split('T')[0] : 'N/A'}
                    </span>
                  </div>
                </div>

                {/* Product Name in Order */}
                <div className="py-2 border-y border-slate-800/50">
                   <span className="text-[9px] text-slate-500 block uppercase font-bold mb-1">Items in Shipment</span>
                   <p className="text-slate-200 text-sm font-medium">
                     {item.products?.[0]?.product_name || "Unknown Product"}
                   </p>
                </div>

                {/* Status Section */}
                {item.order_status === 'Delivered' ? (
                  <div className="bg-emerald-500/10 border border-emerald-500/50 p-2.5 rounded-lg text-center">
                    <span className="text-emerald-500 font-bold text-[10px] uppercase tracking-[0.2em]">
                      Status: Successfully Delivered
                    </span>
                  </div>
                ) : item.order_status === 'Cancelled' ? (
                  <div className="bg-red-500/10 border border-red-500/50 p-2.5 rounded-lg text-center">
                    <span className="text-red-500 font-bold text-[10px] uppercase tracking-[0.2em]">
                      Status: Transaction Cancelled
                    </span>
                  </div>
                ) : (
                  /* Progress Slider for Active Orders */
                  <div className="space-y-3 pt-2">
                    <div className="relative h-1 w-full bg-slate-800 rounded-full overflow-hidden">
                      <div 
                        className="absolute h-full bg-cyan-500 shadow-[0_0_12px_#22d3ee] transition-all duration-1000"
                        style={{ width: `${(getStatusStep(item.order_status) / 3) * 100 + 5}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between items-start text-[8px] font-mono tracking-tighter uppercase">
                      <div className={getStatusStep(item.order_status) >= 0 ? 'text-cyan-400' : 'text-slate-600'}>Placed</div>
                      <div className={getStatusStep(item.order_status) >= 1 ? 'text-cyan-400' : 'text-slate-600'}>Shipped</div>
                      <div className={getStatusStep(item.order_status) >= 2 ? 'text-cyan-400' : 'text-slate-600'}>Tracking</div>
                      <div className="text-slate-600">Delivered</div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Results;