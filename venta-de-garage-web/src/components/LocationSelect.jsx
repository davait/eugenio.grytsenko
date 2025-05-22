import React, { useState, useEffect } from 'react';
import {
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Stack,
} from '@mui/material';
import { fetchLocations } from '../services/api';

const LocationSelect = ({ value, onChange, required = false }) => {
    const [locations, setLocations] = useState({
        provinces: [],
        localities: []
    });
    const [selectedProvince, setSelectedProvince] = useState('');
    const [selectedLocality, setSelectedLocality] = useState('');

    useEffect(() => {
        const loadLocations = async () => {
            try {
                const data = await fetchLocations();
                setLocations(data);
            } catch (error) {
                console.error('Error loading locations:', error);
            }
        };
        loadLocations();
    }, []);

    useEffect(() => {
        // Si hay un valor inicial, establecer las selecciones
        if (value) {
            // Si value es un número o string simple, buscar la provincia correspondiente
            const localityId = value;
            setSelectedLocality(localityId);
            // Buscar la provincia correspondiente a la localidad
            const loc = locations.localities.find(l => String(l.id) === String(localityId));
            if (loc) {
                setSelectedProvince(String(loc.province_id));
            }
        }
    }, [value, locations]);

    const handleProvinceChange = (event) => {
        const provinceId = event.target.value;
        setSelectedProvince(provinceId);
        setSelectedLocality('');
        // No llamar a onChange aquí, solo al seleccionar localidad
    };

    const handleLocalityChange = (event) => {
        const localityId = event.target.value;
        setSelectedLocality(localityId);
        onChange(localityId); // Solo el id de la localidad
    };

    return (
        <Stack direction="row" spacing={2}>
            <FormControl fullWidth required={required}>
                <InputLabel id="province-label">Provincia</InputLabel>
                <Select
                    labelId="province-label"
                    value={selectedProvince}
                    label="Provincia"
                    onChange={handleProvinceChange}
                >
                    {locations.provinces.map((province) => (
                        <MenuItem key={province.id} value={province.id}>
                            {province.name}
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>

            <FormControl fullWidth required={required}>
                <InputLabel id="locality-label">Localidad</InputLabel>
                <Select
                    labelId="locality-label"
                    value={selectedLocality}
                    label="Localidad"
                    onChange={handleLocalityChange}
                    disabled={!selectedProvince}
                >
                    {locations.localities
                        .filter(loc => loc.province_id === parseInt(selectedProvince))
                        .map((locality) => (
                            <MenuItem key={locality.id} value={locality.id}>
                                {locality.name}
                            </MenuItem>
                        ))}
                </Select>
            </FormControl>
        </Stack>
    );
};

export default LocationSelect; 