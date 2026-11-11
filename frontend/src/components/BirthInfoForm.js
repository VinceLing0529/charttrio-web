import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import apiService from '../services/api';

const BirthInfoForm = ({ onCalculated, onError, onLoadingChange }) => {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [timezoneInfo, setTimezoneInfo] = useState(null);
    const [showDaylightSaving, setShowDaylightSaving] = useState(false);

    const {
        register,
        handleSubmit,
        watch,
        setValue,
        getValues,
        formState: { errors }
    } = useForm({
        defaultValues: {
            birth_date: '',
            birth_time: '',
            longitude: '',
            latitude: '',
            gender: '1',
            location_name: '',
            daylight_saving: false
        }
    });

    const genderValue = watch('gender');
    const longitude = watch('longitude');
    const latitude = watch('latitude');

    // 自动获取时区信息
    const handleCoordinatesChange = async () => {
        if (longitude && latitude && !isNaN(longitude) && !isNaN(latitude)) {
            try {
                const timezone = await apiService.getTimezone(parseFloat(longitude), parseFloat(latitude));
                setTimezoneInfo(timezone);
                toast.success(`Timezone detected: ${timezone.timezone} (UTC${timezone.utc_offset >= 0 ? '+' : ''}${timezone.utc_offset})`);
            } catch (error) {
                console.warn('Timezone detection failed:', error.message);
                setTimezoneInfo(null);
            }
        }
    };

    // 提交表单
    const onSubmit = async (data) => {
        setIsSubmitting(true);
        onLoadingChange(true);

        try {
            // 验证经Latitude
            const lng = parseFloat(data.longitude);
            const lat = parseFloat(data.latitude);

            if (isNaN(lng) || lng < -180 || lng > 180) {
                throw new Error('Longitude must be between -180 and 180');
            }

            if (isNaN(lat) || lat < -90 || lat > 90) {
                throw new Error('Latitude must be between -90 and 90');
            }

            // 构建请求数据
            const birthInfo = {
                birth_date: data.birth_date,
                birth_time: data.birth_time,
                longitude: lng,
                latitude: lat,
                gender: parseInt(data.gender),
                location_name: data.location_name || `Longitude ${lng}, Latitude ${lat}`,
                daylight_saving: data.daylight_saving || false
            };

            // 调用API计算命盘
            const result = await apiService.calculateCharts(birthInfo);

            toast.success('Your charts are ready!');
            onCalculated(result);

        } catch (error) {
            console.error('Calculation failed:', error);
            toast.error(error.message);
            onError(error.message);
        } finally {
            setIsSubmitting(false);
            onLoadingChange(false);
        }
    };

    // 使用Use sample
    const useExampleData = () => {
        setValue('birth_date', '2000-01-01');
        setValue('birth_time', '00:00');
        setValue('longitude', '116.4');
        setValue('latitude', '39.9');
        setValue('gender', '1', { shouldValidate: true });
        setValue('location_name', 'Beijing');
        toast.success('Sample details filled in');
    };

    // Popular cities quick-select
    const popularCities = [
        { name: 'New York', longitude: -74.0, latitude: 40.7 },
        { name: 'Los Angeles', longitude: -118.2, latitude: 34.1 },
        { name: 'London', longitude: -0.1, latitude: 51.5 },
        { name: 'Toronto', longitude: -79.4, latitude: 43.7 },
        { name: 'Sydney', longitude: 151.2, latitude: -33.9 },
        { name: 'Singapore', longitude: 103.8, latitude: 1.35 },
    ];

    // Region and city data (English names, for the overseas edition)
    const cityData = {
        'United States': {
            'New York': { longitude: -73.9857, latitude: 40.7484 },
            'Los Angeles': { longitude: -118.2437, latitude: 34.0522 },
            'Chicago': { longitude: -87.6298, latitude: 41.8781 },
            'Houston': { longitude: -95.3698, latitude: 29.7604 },
            'San Francisco': { longitude: -122.4194, latitude: 37.7749 },
            'Seattle': { longitude: -122.3321, latitude: 47.6062 },
            'Miami': { longitude: -80.1918, latitude: 25.7617 },
            'Boston': { longitude: -71.0589, latitude: 42.3601 },
            'Denver': { longitude: -104.9903, latitude: 39.7392 },
            'Honolulu': { longitude: -157.8583, latitude: 21.3069 }
        },
        'Canada': {
            'Toronto': { longitude: -79.3832, latitude: 43.6532 },
            'Vancouver': { longitude: -123.1207, latitude: 49.2827 },
            'Montreal': { longitude: -73.5673, latitude: 45.5017 },
            'Calgary': { longitude: -114.0667, latitude: 51.0447 }
        },
        'United Kingdom': {
            'London': { longitude: -0.1276, latitude: 51.5074 },
            'Manchester': { longitude: -2.2426, latitude: 53.4808 },
            'Edinburgh': { longitude: -3.1883, latitude: 55.9533 }
        },
        'Europe': {
            'Paris': { longitude: 2.3522, latitude: 48.8566 },
            'Berlin': { longitude: 13.4050, latitude: 52.5200 },
            'Rome': { longitude: 12.4964, latitude: 41.9028 },
            'Madrid': { longitude: -3.7038, latitude: 40.4168 },
            'Amsterdam': { longitude: 4.9041, latitude: 52.3676 }
        },
        'China': {
            'Beijing': { longitude: 116.4074, latitude: 39.9042 },
            'Shanghai': { longitude: 121.4737, latitude: 31.2304 },
            'Guangzhou': { longitude: 113.2644, latitude: 23.1291 },
            'Shenzhen': { longitude: 114.0577, latitude: 22.5431 },
            'Chengdu': { longitude: 104.0665, latitude: 30.5723 },
            'Hangzhou': { longitude: 120.1551, latitude: 30.2741 },
            'Hong Kong': { longitude: 114.1694, latitude: 22.3193 },
            'Taipei': { longitude: 121.5654, latitude: 25.0330 }
        },
        'Asia Pacific': {
            'Singapore': { longitude: 103.8198, latitude: 1.3521 },
            'Tokyo': { longitude: 139.6503, latitude: 35.6762 },
            'Seoul': { longitude: 126.9780, latitude: 37.5665 },
            'Mumbai': { longitude: 72.8777, latitude: 19.0760 },
            'Delhi': { longitude: 77.1025, latitude: 28.7041 },
            'Bangkok': { longitude: 100.5018, latitude: 13.7563 }
        },
        'Australia & New Zealand': {
            'Sydney': { longitude: 151.2093, latitude: -33.8688 },
            'Melbourne': { longitude: 144.9631, latitude: -37.8136 },
            'Brisbane': { longitude: 153.0260, latitude: -27.4705 },
            'Perth': { longitude: 115.8589, latitude: -31.9522 },
            'Auckland': { longitude: 174.7633, latitude: -36.8485 }
        }
    };

    const [selectedProvince, setSelectedProvince] = useState('');
    const [selectedCity, setSelectedCity] = useState('');
    const [showLocationSelector, setShowLocationSelector] = useState(false);

    const selectCity = (city) => {
        setValue('longitude', city.longitude.toFixed(1));
        setValue('latitude', city.latitude.toFixed(1));
        setValue('location_name', city.name);
        setValue('daylight_saving', false);
        setShowDaylightSaving(false);
        handleCoordinatesChange();
        toast.success(`${city.name} selected`);
        setShowLocationSelector(false);
    };

    const handleProvinceChange = (province) => {
        setSelectedProvince(province);
        setSelectedCity('');
        setValue('location_name', '');
        setValue('longitude', '');
        setValue('latitude', '');
    };

    const handleCityChange = (cityName) => {
        setSelectedCity(cityName);
        const cityData_selected = cityData[selectedProvince][cityName];
        setValue('longitude', cityData_selected.longitude.toFixed(1));
        setValue('latitude', cityData_selected.latitude.toFixed(1));
        setValue('location_name', cityName);
        setValue('daylight_saving', false);
        setShowDaylightSaving(false);
        handleCoordinatesChange();
        toast.success(`${cityName} selected`);
        setShowLocationSelector(false);
    };

    const showOtherLocationSelector = () => {
        setShowLocationSelector(true);
    };

    const handleOtherLocationSelect = () => {
        setValue('location_name', 'Other location');
        setValue('longitude', '');
        setValue('latitude', '');
        setValue('daylight_saving', false);
        setShowLocationSelector(false);
        setShowDaylightSaving(true);
    };

    return (
        <div className="w-full bg-paper-card border border-line rounded shadow-soft mystical-card">
            <div className="text-center border-b border-line p-5">
                <h2 className="text-xl font-serif font-bold text-ink tracking-wide flex items-center justify-center mb-1">
                    <span className="seal w-6 h-6 text-xs mr-3">录</span>
                    Your Birth Details
                </h2>
                <p className="text-ink-faint text-sm">Enter your birth details as accurately as you can — the closer they are, the sharper the reading.</p>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="p-4 lg:p-6 space-y-3 lg:space-y-4">
                {/* 第一行：Date of Birth、时间、Gender */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Date of Birth */}
                    <div className="space-y-2">
                        <label className="form-label flex items-center">
                            <span className="inline-block w-2 h-2 mr-2 bg-primary-500 rounded-[2px] shrink-0"></span>
                            Date of Birth
                        </label>
                        <input
                            type="date"
                            {...register('birth_date', {
                                required: 'Please choose your birth date',
                                validate: (value) => {
                                    const date = new Date(value);
                                    const now = new Date();
                                    if (date > now) return 'Birth date cannot be in the future';
                                    if (date < new Date('1900-01-01')) return 'Birth date cannot be before 1900';
                                    return true;
                                }
                            })}
                            className="form-input text-sm"
                            style={{
                                colorScheme: 'light'
                            }}
                        />
                        {errors.birth_date && (
                            <p className="form-error text-xs">{errors.birth_date.message}</p>
                        )}
                    </div>

                    {/* Time of Birth */}
                    <div className="space-y-2">
                        <label className="form-label flex items-center">
                            <span className="inline-block w-2 h-2 mr-2 bg-primary-500 rounded-[2px] shrink-0"></span>
                            Time of Birth
                        </label>
                        <input
                            type="time"
                            {...register('birth_time', { required: 'Please choose your birth time' })}
                            className="form-input text-sm"
                            style={{
                                colorScheme: 'light'
                            }}
                        />
                        <p className="text-xs text-ink-faint mt-1">The closer the time, the sharper the chart. Only remember roughly? A close guess still works.</p>
                        {errors.birth_time && (
                            <p className="form-error text-xs">{errors.birth_time.message}</p>
                        )}
                    </div>

                    {/* Gender */}
                    <div className="space-y-2">
                        <label className="form-label flex items-center">
                            <span className="inline-block w-2 h-2 mr-2 bg-primary-500 rounded-[2px] shrink-0"></span>
                            Gender
                        </label>
                        <div className="flex space-x-4 pt-1">
                            <label className="flex items-center space-x-2 cursor-pointer group relative">
                                <input
                                    type="radio"
                                    value="1"
                                    {...register('gender', { required: 'Please select a gender' })}
                                    className="absolute opacity-0 peer"
                                    id="male"
                                />
                                <div className={`w-5 h-5 border rounded-full transition-colors flex items-center justify-center ${genderValue === '1' ? 'border-primary-600 bg-primary-50' : 'border-ink-faint bg-paper-card group-hover:border-primary-400'}`}>
                                    <div className={`w-2.5 h-2.5 rounded-full bg-primary-600 transition-opacity ${genderValue === '1' ? 'opacity-100' : 'opacity-0'}`}></div>
                                </div>
                                <span className={`text-sm transition-colors select-none ${genderValue === '1' ? 'text-primary-700 font-medium' : 'text-ink group-hover:text-primary-700'}`}>Male</span>
                            </label>
                            <label className="flex items-center space-x-2 cursor-pointer group relative">
                                <input
                                    type="radio"
                                    value="0"
                                    {...register('gender', { required: 'Please select a gender' })}
                                    className="absolute opacity-0 peer"
                                    id="female"
                                />
                                <div className={`w-5 h-5 border rounded-full transition-colors flex items-center justify-center ${genderValue === '0' ? 'border-primary-600 bg-primary-50' : 'border-ink-faint bg-paper-card group-hover:border-primary-400'}`}>
                                    <div className={`w-2.5 h-2.5 rounded-full bg-primary-600 transition-opacity ${genderValue === '0' ? 'opacity-100' : 'opacity-0'}`}></div>
                                </div>
                                <span className={`text-sm transition-colors select-none ${genderValue === '0' ? 'text-primary-700 font-medium' : 'text-ink group-hover:text-primary-700'}`}>Female</span>
                            </label>
                        </div>
                        {errors.gender && (
                            <p className="form-error text-xs">{errors.gender.message}</p>
                        )}
                    </div>
                </div>

                {/* 第二行：Place of Birth、经Latitude */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {/* Place of Birth */}
                    <div className="space-y-2">
                        <label className="form-label flex items-center">
                            <span className="inline-block w-2 h-2 mr-2 bg-primary-500 rounded-[2px] shrink-0"></span>
                            Place of Birth
                        </label>
                        <input
                            type="text"
                            placeholder="Choose a city below"
                            {...register('location_name', { required: 'Please choose your birth place' })}
                            className="form-input text-sm"
                            readOnly
                        />
                        {errors.location_name && (
                            <p className="form-error text-xs">{errors.location_name.message}</p>
                        )}
                    </div>

                    {/* Longitude */}
                    <div className="space-y-2">
                        <label className="form-label">Longitude</label>
                        <input
                            type="number"
                            step="0.1"
                            placeholder="e.g. 116.4 (Beijing), -74.0 (New York)"
                            {...register('longitude', {
                                required: 'Please enter the longitude',
                                min: { value: -180, message: 'Longitude range: -180 to 180' },
                                max: { value: 180, message: 'Longitude range: -180 to 180' }
                            })}
                            onChange={handleCoordinatesChange}
                            className="form-input text-sm"
                            readOnly={getValues('location_name') !== 'Other location'}
                        />
                        {errors.longitude && (
                            <p className="form-error text-xs">{errors.longitude.message}</p>
                        )}
                    </div>

                    {/* Latitude */}
                    <div className="space-y-2">
                        <label className="form-label">Latitude</label>
                        <input
                            type="number"
                            step="0.1"
                            placeholder="e.g. 39.9 (Beijing), 40.7 (New York)"
                            {...register('latitude', {
                                required: 'Please enter the latitude',
                                min: { value: -90, message: 'Latitude range: -90 to 90' },
                                max: { value: 90, message: 'Latitude range: -90 to 90' }
                            })}
                            onChange={handleCoordinatesChange}
                            className="form-input text-sm"
                            readOnly={getValues('location_name') !== 'Other location'}
                        />
                        {errors.latitude && (
                            <p className="form-error text-xs">{errors.latitude.message}</p>
                        )}
                    </div>
                </div>

                {/* Quick pick a city */}
                <div className="space-y-2">
                    <label className="form-label">Quick pick a city</label>
                    <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                        {popularCities.map((city) => (
                            <button
                                key={city.name}
                                type="button"
                                onClick={() => selectCity(city)}
                                className="bg-paper-card border border-line text-ink-soft hover:border-primary-400 hover:text-primary-700 transition-colors duration-200 rounded px-2 py-1.5 text-xs"
                            >
                                {city.name}
                            </button>
                        ))}
                        <button
                            type="button"
                            onClick={showOtherLocationSelector}
                            className="bg-accent-50 border border-accent-300 text-accent-800 hover:bg-accent-100 hover:border-accent-400 transition-colors duration-200 rounded px-2 py-1.5 text-xs"
                        >
                            Other location
                        </button>
                    </div>
                </div>

                {/* 省份城市选择器 */}
                {showLocationSelector && (
                    <div className="space-y-3 p-4 bg-paper-deep/60 rounded border border-line">
                        <div className="flex justify-between items-center">
                            <h3 className="text-ink text-sm font-medium font-serif">Choose your region and city</h3>
                            <button
                                type="button"
                                onClick={() => setShowLocationSelector(false)}
                                className="text-ink-faint hover:text-primary-600 text-sm"
                            >
                                ✕
                            </button>
                        </div>

                        {/* 省份选择 */}
                        <div className="space-y-2">
                            <label className="form-label text-xs">Region / Country</label>
                            <select
                                value={selectedProvince}
                                onChange={(e) => handleProvinceChange(e.target.value)}
                                className="form-input text-sm"
                                style={{
                                    colorScheme: 'light'
                                }}
                            >
                                <option value="" className="bg-paper-card text-ink-faint">Select a region</option>
                                {Object.keys(cityData).map((province) => (
                                    <option key={province} value={province} className="bg-paper-card text-ink">{province}</option>
                                ))}
                            </select>
                        </div>

                        {/* 城市选择 */}
                        {selectedProvince && (
                            <div className="space-y-2">
                                <label className="form-label text-xs">City</label>
                                <select
                                    value={selectedCity}
                                    onChange={(e) => handleCityChange(e.target.value)}
                                    className="form-input text-sm"
                                    style={{
                                        colorScheme: 'light'
                                    }}
                                >
                                    <option value="" className="bg-paper-card text-ink-faint">Select a city</option>
                                    {Object.keys(cityData[selectedProvince]).map((city) => (
                                        <option key={city} value={city} className="bg-paper-card text-ink">{city}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        {/* Other location按钮 */}
                        <div className="pt-2">
                            <button
                                type="button"
                                onClick={handleOtherLocationSelect}
                                className="w-full bg-accent-50 border border-accent-300 text-accent-800 hover:bg-accent-100 hover:border-accent-400 px-3 py-2 rounded text-sm transition-colors"
                            >
                                Somewhere else (enter coordinates manually)
                            </button>
                        </div>
                    </div>
                )}

                {/* 时区信息显示 */}
                {timezoneInfo && (
                    <div className="bg-secondary-50 border border-secondary-200 rounded p-3">
                        <p className="text-xs text-secondary-800">
                            <strong>Timezone detected:</strong>{timezoneInfo.timezone}
                            (UTC{timezoneInfo.utc_offset >= 0 ? '+' : ''}{timezoneInfo.utc_offset})
                            {timezoneInfo.estimated && ' (estimated)'}
                        </p>
                    </div>
                )}

                {/* 操作按钮 */}
                <div className="flex space-x-3 pt-3">
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="btn-primary flex-1 text-sm disabled:opacity-60 disabled:cursor-not-allowed"
                    >
                        <span className="flex items-center justify-center">
                            <span className="seal w-5 h-5 text-[10px] mr-2.5">印</span>
                            <span>{isSubmitting ? 'Working...' : 'Cast My Chart'}</span>
                        </span>
                    </button>
                    <button
                        type="button"
                        onClick={useExampleData}
                        disabled={isSubmitting}
                        className="btn-outline text-sm"
                    >
                        Use sample
                    </button>
                </div>
            </form>

            {/* 帮助信息 - 紧凑版 */}
            <div className="mx-4 lg:mx-6 mb-4 lg:mb-5 p-3 lg:p-4 bg-paper-deep/60 rounded border border-line">
                <div className="grid grid-cols-2 gap-4 text-xs text-ink-faint leading-relaxed">
                    <div>
                        <p>• The more exact your birth time, the more precise the reading</p>
                        <p>• Works for birth places anywhere in the world</p>
                    </div>
                    <div>
                        <p>• You can look up coordinates in any map app</p>
                        <p>• Your timezone is detected automatically from the coordinates</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default BirthInfoForm; 