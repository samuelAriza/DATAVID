USE covid_db;

-- Desactivar foreign key checks temporalmente
SET FOREIGN_KEY_CHECKS = 0;

-- Limpiar tablas existentes
TRUNCATE TABLE hospitales;
TRUNCATE TABLE municipios;
TRUNCATE TABLE departamentos;

-- Reactivar foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- Insertar los 36 departamentos de Colombia con datos reales
INSERT INTO departamentos (id_departamento, nombre_departamento, codigo_dane, poblacion_2020, area_km2, densidad_poblacional, region, capital) VALUES 
-- Región Andina
(5, 'ANTIOQUIA', '05', 6677930, 63612, 105, 'Andina', 'Medellín'),
(11, 'BOGOTA D.C.', '11', 7743955, 1587, 4880, 'Andina', 'Bogotá'),
(15, 'BOYACA', '15', 1276407, 23189, 55, 'Andina', 'Tunja'),
(17, 'CALDAS', '17', 987991, 7888, 125, 'Andina', 'Manizales'),
(25, 'CUNDINAMARCA', '25', 3242999, 22623, 143, 'Andina', 'Bogotá'),
(41, 'HUILA', '41', 1206371, 19890, 61, 'Andina', 'Neiva'),
(63, 'QUINDIO', '63', 565310, 1845, 306, 'Andina', 'Armenia'),
(66, 'RISARALDA', '66', 965111, 4140, 233, 'Andina', 'Pereira'),
(68, 'SANTANDER', '68', 2184837, 30537, 72, 'Andina', 'Bucaramanga'),
(73, 'TOLIMA', '73', 1408272, 23562, 60, 'Andina', 'Ibagué'),
(54, 'NORTE DE SANTANDER', '54', 1485026, 21658, 69, 'Andina', 'Cúcuta'),

-- Región Caribe
(8, 'ATLANTICO', '08', 2535517, 3388, 748, 'Caribe', 'Barranquilla'),
(13, 'BOLIVAR', '13', 2207865, 25978, 85, 'Caribe', 'Cartagena'),
(20, 'CESAR', '20', 1295494, 22905, 57, 'Caribe', 'Valledupar'),
(23, 'CORDOBA', '23', 1828947, 23980, 76, 'Caribe', 'Montería'),
(44, 'LA GUAJIRA', '44', 1032084, 20848, 49, 'Caribe', 'Riohacha'),
(47, 'MAGDALENA', '47', 1414661, 23188, 61, 'Caribe', 'Santa Marta'),
(70, 'SUCRE', '70', 926509, 10917, 85, 'Caribe', 'Sincelejo'),
(88, 'SAN ANDRES', '88', 78492, 52, 1509, 'Caribe', 'San Andrés'),

-- Región Pacífica
(19, 'CAUCA', '19', 1464488, 29308, 50, 'Pacífica', 'Popayán'),
(27, 'CHOCO', '27', 534826, 46530, 11, 'Pacífica', 'Quibdó'),
(52, 'NARIÑO', '52', 1627589, 33268, 49, 'Pacífica', 'Pasto'),
(76, 'VALLE DEL CAUCA', '76', 4660600, 22140, 210, 'Pacífica', 'Cali'),

-- Región Orinoquía
(81, 'ARAUCA', '81', 262174, 23818, 11, 'Orinoquía', 'Arauca'),
(85, 'CASANARE', '85', 401609, 44640, 9, 'Orinoquía', 'Yopal'),
(50, 'META', '50', 1080831, 85635, 13, 'Orinoquía', 'Villavicencio'),
(99, 'VICHADA', '99', 107808, 100242, 1, 'Orinoquía', 'Puerto Carreño'),

-- Región Amazonía
(91, 'AMAZONAS', '91', 80271, 109665, 1, 'Amazonía', 'Leticia'),
(18, 'CAQUETA', '18', 505383, 88965, 6, 'Amazonía', 'Florencia'),
(94, 'GUAINIA', '94', 49528, 72238, 1, 'Amazonía', 'Inírida'),
(95, 'GUAVIARE', '95', 116974, 53460, 2, 'Amazonía', 'San José del Guaviare'),
(86, 'PUTUMAYO', '86', 360711, 24885, 14, 'Amazonía', 'Mocoa'),
(97, 'VAUPES', '97', 46858, 54135, 1, 'Amazonía', 'Mitú');

-- Insertar algunos municipios principales
INSERT INTO municipios (id_municipio, id_departamento, nombre_municipio, codigo_dane, poblacion_2020, altitud_msnm, categoria) VALUES
-- Antioquia
(5001, 5, 'MEDELLIN', '05001', 2569007, 1495, 'Especial'),
(5002, 5, 'ENVIGADO', '05266', 244986, 1575, '1'),
(5088, 5, 'ITAGUI', '05360', 281853, 1640, '1'),
(5079, 5, 'BELLO', '05088', 506419, 1450, '1'),

-- Bogotá
(11001, 11, 'BOGOTA D.C.', '11001', 7743955, 2640, 'Especial'),

-- Valle del Cauca
(76001, 76, 'CALI', '76001', 2258653, 1018, 'Especial'),
(76111, 76, 'BUENAVENTURA', '76109', 442291, 7, '2'),
(76364, 76, 'PALMIRA', '76520', 319841, 1001, '2'),

-- Atlántico
(8001, 8, 'BARRANQUILLA', '08001', 1274250, 18, 'Especial'),
(8141, 8, 'SOLEDAD', '08758', 650753, 23, '1'),

-- Bolívar
(13001, 13, 'CARTAGENA', '13001', 1028736, 2, 'Especial'),
(13244, 13, 'MAGANGUE', '13430', 127906, 17, '3'),

-- Santander
(68001, 68, 'BUCARAMANGA', '68001', 613400, 959, 'Especial'),
(68276, 68, 'FLORIDABLANCA', '68276', 274990, 931, '1'),

-- Norte de Santander
(54001, 54, 'CUCUTA', '54001', 777106, 320, 'Especial'),
(54498, 54, 'OCAÑA', '54498', 96881, 1202, '3'),

-- Cundinamarca
(25754, 25, 'SOACHA', '25754', 731020, 2566, '1'),
(25286, 25, 'FACATATIVA', '25269', 142570, 2586, '2'),
(25175, 25, 'CHIA', '25175', 132691, 2564, '2'),

-- Magdalena
(47001, 47, 'SANTA MARTA', '47001', 530326, 6, 'Especial'),
(47258, 47, 'CIENAGA', '47170', 104987, 3, '3'),

-- Nariño
(52001, 52, 'PASTO', '52001', 439404, 2527, 'Especial'),
(52356, 52, 'IPIALES', '52356', 145081, 2898, '3'),

-- Cauca
(19001, 19, 'POPAYAN', '19001', 318059, 1738, 'Especial'),

-- Tolima
(73001, 73, 'IBAGUE', '73001', 553524, 1285, 'Especial'),

-- Meta
(50001, 50, 'VILLAVICENCIO', '50001', 553350, 467, 'Especial'),

-- Huila
(41001, 41, 'NEIVA', '41001', 357392, 442, 'Especial'),

-- Cesar
(20001, 20, 'VALLEDUPAR', '20001', 492308, 200, 'Especial'),

-- Córdoba
(23001, 23, 'MONTERIA', '23001', 502656, 18, 'Especial'),

-- Risaralda
(66001, 66, 'PEREIRA', '66001', 488839, 1411, 'Especial'),

-- Quindío
(63001, 63, 'ARMENIA', '63001', 299476, 1551, 'Especial'),

-- Caldas
(17001, 17, 'MANIZALES', '17001', 402156, 2150, 'Especial'),

-- Sucre
(70001, 70, 'SINCELEJO', '70001', 280970, 213, 'Especial'),

-- La Guajira
(44001, 44, 'RIOHACHA', '44001', 285953, 6, 'Especial'),

-- Boyacá
(15001, 15, 'TUNJA', '15001', 203871, 2820, 'Especial'),

-- Caquetá
(18001, 18, 'FLORENCIA', '18001', 178691, 242, 'Especial'),

-- Casanare
(85001, 85, 'YOPAL', '85001', 147741, 350, 'Especial'),

-- Arauca
(81001, 81, 'ARAUCA', '81001', 90589, 128, 'Especial'),

-- Putumayo
(86001, 86, 'MOCOA', '86001', 42841, 655, 'Especial'),

-- San Andrés
(88001, 88, 'SAN ANDRES', '88001', 78492, 2, 'Especial'),

-- Amazonas
(91001, 91, 'LETICIA', '91001', 48820, 96, 'Especial'),

-- Guainía
(94001, 94, 'INIRIDA', '94001', 19440, 95, 'Especial'),

-- Guaviare
(95001, 95, 'SAN JOSE DEL GUAVIARE', '95001', 64008, 180, 'Especial'),

-- Vaupés
(97001, 97, 'MITU', '97001', 17263, 180, 'Especial'),

-- Vichada
(99001, 99, 'PUERTO CARREÑO', '99001', 16857, 52, 'Especial'),

-- Chocó
(27001, 27, 'QUIBDO', '27001', 119568, 43, 'Especial');

-- Insertar hospitales principales
INSERT INTO hospitales (nombre, id_municipio, nivel_atencion, camas_uci, camas_general, tipo_institucion) VALUES
-- Medellín
('Hospital Pablo Tobón Uribe', 5001, 'Alto', 120, 450, 'Privado'),
('Clínica Las Américas', 5001, 'Alto', 80, 300, 'Privado'),
('Hospital General de Medellín', 5001, 'Medio', 50, 400, 'Público'),

-- Bogotá
('Hospital El Tunal', 11001, 'Alto', 90, 500, 'Público'),
('Fundación Santa Fe de Bogotá', 11001, 'Alto', 150, 600, 'Privado'),
('Hospital Simón Bolívar', 11001, 'Alto', 85, 550, 'Público'),
('Clínica del Country', 11001, 'Alto', 100, 400, 'Privado'),

-- Cali
('Hospital Universitario del Valle', 76001, 'Alto', 110, 650, 'Público'),
('Clínica Valle del Lili', 76001, 'Alto', 140, 550, 'Privado'),

-- Barranquilla
('Clínica de la Costa', 8001, 'Alto', 70, 350, 'Privado'),
('Hospital Universidad del Norte', 8001, 'Alto', 60, 400, 'Privado'),

-- Cartagena
('Hospital Universitario del Caribe', 13001, 'Alto', 65, 450, 'Público'),

-- Bucaramanga
('Clínica FOSCAL', 68001, 'Alto', 75, 380, 'Privado'),

-- Cúcuta
('Hospital Universitario Erasmo Meoz', 54001, 'Alto', 50, 420, 'Público'),

-- Pereira
('Hospital San Jorge', 66001, 'Alto', 55, 320, 'Privado'),

-- Manizales
('Hospital Santa Sofía', 17001, 'Alto', 45, 310, 'Público'),

-- Neiva
('Hospital Universitario Hernando Moncaleano', 41001, 'Medio', 35, 280, 'Público'),

-- Pasto
('Hospital Universitario Departamental de Nariño', 52001, 'Medio', 40, 350, 'Público');