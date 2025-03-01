import requests
from bs4 import BeautifulSoup
import time
import random
import pandas as pd
from datetime import datetime, timedelta
import re
import os

class BookingPriceTracker:
    def __init__(self):
        # Headers para simular un navegador real
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://www.booking.com/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def search_specific_hotel(self, hotel_name, destination, check_in_date, check_out_date):
        """
        Busca un hotel específico por nombre

        """
        # Convertir fechas al formato usado por Booking
        checkin_year, checkin_month, checkin_day = check_in_date.split('-')
        checkout_year, checkout_month, checkout_day = check_out_date.split('-')
        
        # Construir URL de busqueda
        url = "https://www.booking.com/searchresults.es.html"
        params = {
            'ss': f"{hotel_name} {destination}", 
            'checkin_year': checkin_year,
            'checkin_month': checkin_month,
            'checkin_monthday': checkin_day,
            'checkout_year': checkout_year,
            'checkout_month': checkout_month,
            'checkout_monthday': checkout_day,
            'group_adults': 2,
            'no_rooms': 1,
            'group_children': 0,
            'sb': 1,
            'src': 'searchresults',
            'src_elem': 'sb'
        }
        
        print(f"Buscando el hotel: '{hotel_name}' en {destination}...")
        response = self.session.get(url, params=params)
        
        if response.status_code != 200:
            print(f"Error en la búsqueda: {response.status_code}")
            return None
        
        # Analizar la página de resultados
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar el primer resultado que coincida con el nombre del hotel
        # Intentar varios selectores posibles
        hotel_elements = soup.select('[data-testid="property-card"]')
        if not hotel_elements:
            hotel_elements = soup.select('.sr_property_block')
        if not hotel_elements:
            hotel_elements = soup.select('.sr-hotel__row')
        if not hotel_elements:
            hotel_elements = soup.select('.a826ba81c4')
        
        print(f"Se encontro {hotel_elements}")
        
        for hotel in hotel_elements:
            # Intentar diferentes selectores para el nombre del hotel
            hotel_name_elem = None
            for selector in ['[data-testid="title"]', '.sr-hotel__name', '.hotel_name_link', '.fcab3ed991', '.e13098a59f']:
                hotel_name_elem = hotel.select_one(selector)
                if hotel_name_elem:
                    break
            
            if hotel_name_elem and hotel_name.lower() in hotel_name_elem.text.lower():
                # Encontrar enlace al hotel
                link_elem = None
                for selector in ['[data-testid="title-link"]', '.hotel_name_link', '.sr-hotel__name a', 'a.e13098a59f', '.fcab3ed991 a']:
                    link_elem = hotel.select_one(selector)
                    if link_elem and 'href' in link_elem.attrs:
                        break
                
                if link_elem and 'href' in link_elem.attrs:
                    hotel_url = link_elem['href']
                    
                    if not hotel_url.startswith('http'):
                        hotel_url = 'https://www.booking.com' + hotel_url
                    
                    print(f"Hotel encontrado: {hotel_name_elem.text.strip()}")
                    return hotel_url
        
        print(f"No se encontró el hotel '{hotel_name}' en los resultados.")
        return None
    
    def extract_price(self, hotel_url, check_in_date, check_out_date):
        """
        Extrae el precio de un hotel para las fechas específicas
        
        """
        # Añadir parámetros de fecha a la URL
        checkin_year, checkin_month, checkin_day = check_in_date.split('-')
        checkout_year, checkout_month, checkout_day = check_out_date.split('-')
        
        # Construir URL con parámetros
        if '?' in hotel_url:
            hotel_url += '&'
        else:
            hotel_url += '?'
        
        hotel_url += (
            f"checkin={check_in_date}&"
            f"checkout={check_out_date}&"
            f"group_adults=2&no_rooms=1&group_children=0"
        )
        
        # Añadir un delay para evitar bloqueos
        time.sleep(random.uniform(2, 4))
        
        print(f"Consultando precio para {check_in_date} hasta {check_out_date}...")
        response = self.session.get(hotel_url)
        
        if response.status_code != 200:
            print(f"Error al obtener la página del hotel: {response.status_code}")
            return {
                'fecha_entrada': check_in_date,
                'fecha_salida': check_out_date,
                'precio': 'Error',
                'estado': 'Error'
            }
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extraer nombre del hotel (intenta múltiples selectores)
        hotel_name = "Hotel"
        for selector in ['h2.pp-header__title', '.hp__hotel-name', '[data-testid="property-header"] h2', '.d2fee87262', '.pp-header__title']:
            name_elem = soup.select_one(selector)
            if name_elem:
                hotel_name = name_elem.text.strip()
                break
        
        # Extraer precio
        price = "No disponible"
        
        # Estrategia 1: Buscar selectores específicos de precio
        price_selectors = [
            'span.prco-valign-middle-helper',
            '.prco-wrapper .bui-price-display__value',
            '[data-testid="price-and-discounted-price"]',
            '.hprt-price-price',
            '.bui-price-display__value',
            '.cb5ebe3ffb',
            '.fcab3ed991',
            '.fbd1d3018c',
            '[data-testid="price-for-x-nights"]'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = price_elem.text.strip()
                break
        
        # # Estrategia 2: Buscar por atributos de datos
        # if price == "No disponible":
        #     for elem in soup.find_all(attrs={"data-testid": re.compile(".*price.*")}):
        #         price = elem.text.strip()
        #         break
        
        # # Estrategia 3: Buscar en scripts JSON
        # if price == "No disponible":
        #     # Intentar extraer precio de scripts JSON
        #     script_tags = soup.find_all('script', type='application/ld+json')
        #     for script in script_tags:
        #         try:
        #             import json
        #             data = json.loads(script.string)
        #             if 'offers' in data and 'price' in data['offers']:
        #                 price = str(data['offers']['price']) + ' ' + data['offers']['priceCurrency']
        #                 break
        #         except:
        #             continue
        
        # # Estrategia 4: Buscar texto que parezca precio con regex
        # if price == "No disponible":
        #     # Buscar patrones de texto que parezcan precios
        #     price_patterns = [
        #         r'€\s*\d+[.,]\d+',
        #         r'\d+[.,]\d+\s*€',
        #         r'\$\s*\d+[.,]\d+',
        #         r'\d+[.,]\d+\s*\$'
        #     ]
            
        #     for pattern in price_patterns:
        #         price_matches = re.findall(pattern, soup.text)
        #         if price_matches:
        #             price = price_matches[0].strip()
        #             break
        
        # Comprobar disponibilidad
        availability = "Disponible"
        sold_out_selectors = ['.sold_out_property', '[data-testid="no-availability-label"]', '.fe_banner__message']
        for selector in sold_out_selectors:
            if soup.select_one(selector):
                availability = "No disponible"
                break
        
        # Si no hay precio pero está disponible, es probablemente un problema de extracción
        if price == "No disponible" and availability == "Disponible":
            price = "Error de extracción - Ver sitio web"
        
        return {
            'hotel': hotel_name,
            'fecha_entrada': check_in_date,
            'fecha_salida': check_out_date,
            'precio': price,
            'estado': availability,
            'url': hotel_url
        }
    
    def track_prices_weekly(self, hotel_name, destination, start_date, num_weeks):
        """
        Hace seguimiento de precios de un hotel específico cada 7 días
        
        """
        # Convertir fecha inicial a objeto datetime
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        
        # Buscar el hotel la primera vez
        first_checkout = (start_date_obj + timedelta(days=6)).strftime("%Y-%m-%d")
        hotel_url = self.search_specific_hotel(hotel_name, destination, start_date, first_checkout)
        
        if not hotel_url:
            print(f"No se pudo encontrar el hotel '{hotel_name}'. Finalizando búsqueda.")
            return []
        
        # Limpiar la URL de parámetros de fecha para evitar conflictos
        if '?' in hotel_url:
            hotel_url = hotel_url.split('?')[0]
        
        results = []
        
        # Consultar precios para cada semana (loop)
        for week in range(num_weeks):
            checkin_date = (start_date_obj + timedelta(days=6 * week)).strftime("%Y-%m-%d")
            checkout_date = (start_date_obj + timedelta(days=6 * (week + 1))).strftime("%Y-%m-%d")
            
            price_info = self.extract_price(hotel_url, checkin_date, checkout_date)
            results.append(price_info)
            
            print(f"Semana {week+1}: {checkin_date} a {checkout_date} - Precio: {price_info['precio']}")
            
            # Añadir delay entre solicitudes
            time.sleep(random.uniform(3, 5))
        
        return results
    
    # def save_to_excel(self, price_data, filename=None):
    #     """
    #     Guarda los datos de precios en un archivo Excel (.xlsx)
        
    #     """
    #     if not price_data:
    #         print("No hay datos para guardar.")
    #         return
        
    #     if not filename:
    #         current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    #         hotel_name = price_data[0]['hotel'].replace(' ', '_')
    #         filename = f"{hotel_name}_precios_{current_time}.xlsx"
        
    #     # # Comprobar si el nombre del archivo tiene la extensión .xlsx
    #     # if not filename.endswith('.xlsx'):
    #     #     filename += '.xlsx'
        
    #     # Crear un DataFrame con pandas
    #     df = pd.DataFrame(price_data)
        
    #     # Guardar en Excel con formato
    #     try:
    #         # Crear un ExcelWriter
    #         with pd.ExcelWriter(filename, engine='openpyxl') as writer:
    #             # Escribir el DataFrame en una hoja llamada 'Precios'
    #             df.to_excel(writer, sheet_name='Precios', index=False)
                
    #             # Obtener el objeto workbook y worksheet
    #             workbook = writer.book
    #             worksheet = writer.sheets['Precios']
                
                # # Ajustar el ancho de las columnas automáticamente
                # for column in worksheet.columns:
                #     max_length = 0
                #     column_letter = column[0].column_letter
                #     for cell in column:
                #         if cell.value:
                #             max_length = max(max_length, len(str(cell.value)))
                #     adjusted_width = max_length + 2
                #     worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # # Formatear como tabla
                # from openpyxl.styles import Font, PatternFill, Border, Side
                
                # # Dar formato a los encabezados
                # header_font = Font(bold=True, color='FFFFFF')
                # header_fill = PatternFill(start_color='4F81BD', end_color='4F81BD', fill_type='solid')
                # border = Border(
                #     left=Side(style='thin'), 
                #     right=Side(style='thin'), 
                #     top=Side(style='thin'), 
                #     bottom=Side(style='thin')
                # )
                
                # for cell in worksheet[1]:
                #     cell.font = header_font
                #     cell.fill = header_fill
                #     cell.border = border
                
                # # Formatear cada fila con bordes
                # for row in worksheet.iter_rows(min_row=2, max_row=len(price_data) + 1):
                #     for cell in row:
                #         cell.border = border
                        
                #         # Colorear las celdas según disponibilidad
                #         if cell.column_letter == 'E':  # Columna 'estado'
                #             if cell.value == 'Disponible':
                #                 cell.fill = PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
                #             elif cell.value == 'No disponible':
                #                 cell.fill = PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
            
            # print(f"Datos guardados en {filename}")
            
            # # Abrir el archivo Excel automáticamente (solo en Windows)
            # if os.name == 'nt':  # Windows
            #     os.system(f'start excel "{filename}"')
            # elif os.name == 'posix':  # Mac o Linux
            #     if os.uname().sysname == 'Darwin':  # Mac
            #         os.system(f'open "{filename}"')
            #     else:  # Linux
            #         os.system(f'xdg-open "{filename}"')
            
        # except Exception as e:
        #     print(f"Error al guardar el archivo Excel: {e}")
            
            # # Plan B: Guardar sin formato si hay error
            # try:
            #     df.to_excel(filename, index=False)
            #     print(f"Se guardó una versión simple en {filename}")
            # except:
            #     print("No se pudo guardar el archivo Excel. Verifica tener instalado openpyxl o pandas.")

    def save_to_csv(self, price_data, filename=None):
        """
        Guarda los datos de precios en un archivo CSV (como respaldo)
        
        Args:
            price_data (list): Lista de diccionarios con información de precios
            filename (str): Nombre del archivo CSV (opcional)
        """
        if not price_data:
            print("No hay datos para guardar.")
            return
        
        if not filename:
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            hotel_name = price_data[0]['hotel'].replace(' ', '_')
            filename = f"{hotel_name}_precios_{current_time}.csv"
        
        # Crear un DataFrame con pandas
        df = pd.DataFrame(price_data)
        
        # Guardar en CSV
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"Datos guardados en CSV: {filename}")
