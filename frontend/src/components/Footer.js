import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-ink text-paper/80 mt-auto flex-shrink-0">
            <div className="container mx-auto px-4 lg:px-6 py-8">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div>
                        <h3 className="text-base font-serif font-bold text-paper mb-2 tracking-widest">ChartTrio</h3>
                        <p className="text-paper/60 text-xs leading-relaxed">
                            Three ancient systems, read together: Chinese BaZi, Zi Wei star astrology, and Vedic astrology — one cross-checked reading of your birth chart, in plain words.
                        </p>
                    </div>

                    <div>
                        <h3 className="text-base font-serif font-bold text-paper mb-2 tracking-widest">How It Works</h3>
                        <ul className="text-paper/60 text-xs space-y-1.5">
                            <li>Three-chart cross-checking engine</li>
                            <li>True solar time correction</li>
                            <li>Automatic timezone detection, worldwide</li>
                            <li>Interactive personality mind map</li>
                            <li>Plain-words report engine</li>
                        </ul>
                    </div>

                    <div>
                        <h3 className="text-base font-serif font-bold text-paper mb-2 tracking-widest">Please Note</h3>
                        <p className="text-paper/60 text-xs leading-relaxed">
                            Readings here are drawn from traditional astrology and are meant for reflection and entertainment — never as the sole basis for a major life decision. Your fate stays in your own hands, and a clear head beats any chart.
                        </p>
                    </div>
                </div>

                <div className="border-t border-paper/15 mt-6 pt-4 flex flex-col md:flex-row justify-between items-center gap-1">
                    <p className="text-paper/40 text-xs">ChartTrio Team</p>
                    <a
                        href="mailto:support@charttrio.com"
                        className="text-paper/40 text-xs hover:text-paper/80 transition-colors"
                    >
                        Support · support@charttrio.com
                    </a>
                    <p className="text-paper/40 text-xs">© 2026 ChartTrio</p>
                </div>
            </div>
        </footer>
    );
};

export default Footer;
