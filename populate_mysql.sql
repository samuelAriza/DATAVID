USE covid_db;

CREATE TABLE IF NOT EXISTS departamentos (
    id_departamento INT PRIMARY KEY,
    nombre_departamento VARCHAR(100),
    codigo_dane VARCHAR(10),
    poblacion_2020 INT,
    area_km2 FLOAT,
    densidad_poblacional FLOAT,
    region VARCHAR(50),
    capital VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS municipios (
    id_municipio INT PRIMARY KEY,
    id_departamento INT,
    nombre_municipio VARCHAR(100),
    codigo_dane VARCHAR(10),
    poblacion_2020 INT,
    altitud_msnm INT,
    categoria VARCHAR(20),
    FOREIGN KEY (id_departamento) REFERENCES departamentos(id_departamento)
);

CREATE TABLE IF NOT EXISTS hospitales (
    id_hospital INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(200),
    id_municipio INT,
    nivel_atencion VARCHAR(50),
    camas_uci INT,
    camas_general INT,
    tipo_institucion VARCHAR(50),
    FOREIGN KEY (id_municipio) REFERENCES municipios(id_municipio)
);

-- Insertar datos de ejemplo (datos reales aproximados)
INSERT INTO departamentos VALUES 
(5, 'ANTIOQUIA', '05', 6677930, 63612, 105, 'Andina', 'Medellín'),
(11, 'BOGOTA D.C.', '11', 7743955, 1587, 4880, 'Andina', 'Bogotá'),
(76, 'VALLE DEL CAUCA', '76', 4660600, 22140, 210, 'Pacífica', 'Cali'),
(8, 'ATLANTICO', '08', 2535517, 3388, 748, 'Caribe', 'Barranquilla'),
(13, 'BOLIVAR', '13', 2207865, 25978, 85, 'Caribe', 'Cartagena'),
(17, 'CALDAS', '17', 987991, 7888, 125, 'Andina', 'Manizales'),
(19, 'CAUCA', '19', 1464488, 29308, 50, 'Pacífica', 'Popayán'),
(23, 'CORDOBA', '23', 1828947, 23980, 76, 'Caribe', 'Montería'),
(25, 'CUNDINAMARCA', '25', 3242999, 22623, 143, 'Andina', 'Bogotá'),
(41, 'HUILA', '41', 1206371, 19890, 61, 'Andina', 'Neiva');

INSERT INTO municipios VALUES
(5001, 5, 'MEDELLIN', '05001', 2569007, 1495, 'Especial'),
(5002, 5, 'ENVIGADO', '05266', 244986, 1575, '1'),
(5088, 5, 'ITAGUI', '05360', 281853, 1640, '1'),
(11001, 11, 'BOGOTA D.C.', '11001', 7743955, 2640, 'Especial'),
(76001, 76, 'CALI', '76001', 2258653, 1018, 'Especial');

INSERT INTO hospitales (nombre, id_municipio, nivel_atencion, camas_uci, camas_general, tipo_institucion) VALUES
('Hospital Pablo Tobón Uribe', 5001, 'Alto', 120, 450, 'Privado'),
('Clínica Las Américas', 5001, 'Alto', 80, 300, 'Privado'),
('Hospital General de Medellín', 5001, 'Medio', 50, 400, 'Público'),
('Hospital El Tunal', 11001, 'Alto', 90, 500, 'Público'),
('Fundación Santa Fe de Bogotá', 11001, 'Alto', 150, 600, 'Privado');