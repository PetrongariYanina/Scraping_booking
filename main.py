from scraping import BookingPriceTracker
import requests
from datetime import datetime

if __name__ == "__main__":
    tracker = BookingPriceTracker()
    
    # Configuración de la búsqueda
    hotel_name = "Hotel Riu Papayas - All Inclusive"  
    destination = "Playa del Inglés"  
    #start_date = datetime.now().strftime("%Y-%m-%d")  
    start_date = '2025-03-15'

    num_weeks = 2
    
    # Ejecutar seguimiento de precios
    price_data = tracker.track_prices_weekly(
        hotel_name=hotel_name,
        destination=destination,
        start_date=start_date,
        num_weeks=num_weeks
    )
    
    # Mostrar y guardar resultados
    if price_data:
        print("\nResumen de precios encontrados:")
        for i, data in enumerate(price_data, 1):
            print(f"\n{i}. Semana: {data['fecha_entrada']} - {data['fecha_salida']}")
            print(f"   Hotel: {data['hotel']}")
            print(f"   Precio: {data['precio']}")
            print(f"   Estado: {data['estado']}")
            print(f"   URL: {data['url']}")
        
        # Guardar en Excel
        #tracker.save_to_excel(price_data)
        # # También guardamos en CSV como respaldo
        tracker.save_to_csv(price_data)
    else:
        print("No se pudieron obtener datos de precios.")