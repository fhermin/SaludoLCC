import React, { useEffect, useState } from 'react';
import Icons from './Icons';

function WeatherApp() {
  const [search, setSearch] = useState('hermosillo');
  const [values, setValues] = useState('');
  const [icon, setIcon] = useState('');

  const URL = `https://api.openweathermap.org/data/2.5/weather?q=${search}&lang=es&units=metric&appid=5e3cab27be934736fbedd48ca994b261`;
 // Realiza una solicitud a la API de noticias
  const getData = async () => {
    await fetch(URL)
      .then(response => response.json())
      .then(data => {
        if (data.cod >= 400) {
          setValues(false);
        } else {
          setIcon(data.weather[0].main);
          setValues(data);
        }
      })
      .catch(error => {
        console.log(error);
      });
  };

  const handleSearch = (e) => {
    if (e.key === 'Enter') {
      setSearch(e.target.value);
    }
  };

  useEffect(() => {
    getData();
  }, [search]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="container">
      

      <div className='card'>
        {(values) ? (
          <div className='card-container'>
            <h1 className='city-name'>{values.name}</h1>
            <p className='temp'>{values.main.temp.toFixed(0)}&deg;</p>
            <img className='icon' src={Icons(icon)} alt="icon-weather" />
            <div className='card-footer'>
              <p className='temp-max-min'>{values.main.temp_min.toFixed(0)}&deg;  |  {values.main.temp_max.toFixed(0)}&deg;</p>
            </div>
          </div>
        ) : (
          <h1>{"City not found"}</h1>
        )}
      </div>
    </div>
  );
}

export default WeatherApp;