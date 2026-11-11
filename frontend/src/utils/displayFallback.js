// Fallback for charts cached before the backend gained its English display
// tree (data.display): builds the same shape from the raw chart data, using
// the raw values as display text. Fresh charts always carry the translated
// display tree from the backend, so this only keeps older saved results
// rendering instead of breaking.
const seg = (v) => (v && typeof v === 'object' && !Array.isArray(v) ? v : {});
const list = (v) => (Array.isArray(v) ? v : []);
const item = (raw) => ({ text: raw || '', key: raw || '' });

export function buildDisplayFallback(data) {
    const input = seg(data?.input);
    const bazi = seg(data?.bazi);
    const ziwei = seg(data?.ziwei);

    const detail = list(seg(bazi.enhanced_analysis)['四柱详析']);
    const nayin = seg(bazi.nayin);
    const tenGods = seg(bazi.ten_gods);
    const labels = ['年柱', '月柱', '日柱', '时柱'];
    const keys = ['year', 'month', 'day', 'hour'];
    const pillars = keys.map((key, i) => {
        const raw = bazi[`${key}_pillar`] || '';
        const det = seg(detail[i]);
        return {
            key,
            label: labels[i],
            pair: raw,
            stem: item(raw[0] || ''),
            branch: item(raw[1] || ''),
            nayin: det['纳音'] || nayin[labels[i]] || '',
            hidden_stems: list(det['藏干']).map(item),
            hidden_gods: list(det['藏干十神']).map((hg) => ({
                stem: item(seg(hg)['藏干']),
                god: item(seg(hg)['十神']),
            })),
            ten_god: item(tenGods[`${labels[i][0]}干`] || ''),
            main_god: item(det['主星'] || ''),
            growth_state: det['星运（十二长生）'] || '',
            void: det['空亡'] || '',
        };
    });

    const palacesRaw = seg(seg(ziwei.chart).palaces);
    const palaces = Object.entries(palacesRaw).map(([name, pal]) => {
        const p = seg(pal);
        return {
            name: item(name),
            index: p.index,
            is_body_palace: !!p.is_body_palace,
            stem: item(p.heavenly_stem || ''),
            branch: item(p.earthly_branch || ''),
            major_stars: list(p.major_stars).map((s) => ({
                name: item(seg(s).name || ''),
                brightness: seg(s).brightness || null,
                mutagen: seg(s).mutagen ? item(seg(s).mutagen) : null,
            })),
            minor_stars: list(p.minor_stars).map(item),
            adjective_stars: list(p.adjective_stars).map(item),
        };
    });

    return {
        gender: input.gender_str || '',
        bazi: {
            pillars,
            day_master: item(bazi.day_master || ''),
            body_strength: bazi.body_strength || '',
            five_elements: Object.entries(seg(bazi.five_elements)).map(([k, v]) => ({ key: k, text: k, count: v })),
            ten_gods: Object.entries(tenGods).map(([pos, god]) => ({ position: pos, god: item(god) })),
            spirits: list(bazi.spirits).map(item),
            dayun: {
                direction: seg(bazi.dayun).direction || '',
                qiyun_age: seg(bazi.dayun).qiyun_age,
                note: seg(bazi.dayun).note || '',
            },
            lunar_date: null,
        },
        ziwei: {
            basic: {
                soul: item(seg(ziwei.basic_info).soul || ''),
                body: item(seg(ziwei.basic_info).body || ''),
                five_elements_class: seg(ziwei.basic_info).five_elements_class || '',
                lunar_date: seg(ziwei.basic_info).lunar_date || null,
                chinese_date: seg(ziwei.basic_info).chinese_date || '',
            },
            year_four_trans: Object.entries(seg(ziwei.year_four_trans)).map(([t, s]) => ({
                type: item(t),
                star: item(s),
            })),
            star_positions: Object.entries(seg(seg(ziwei.chart).star_positions)).map(([star, pal]) => ({
                star: item(star),
                palace: item(pal),
            })),
            palaces,
            flow: {},
            features: {},
        },
        vedic: {},
    };
}

export default buildDisplayFallback;
