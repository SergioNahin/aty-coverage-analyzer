// Tipos de datos
interface Stop {
    stop_id: string;
    stop_name: string;
    stop_lat: number;
    stop_lon: number;
  }
  
  interface Route {
    route_id: string;
    route_long_name: string;
  }
  
  interface AlternativeRoute {
    origen: string;
    destino: string;
    ruta_principal: string;
    ruta_alterna: string;
    tiempo_estimado: number;
    transbordos: string[];
  }
  
  interface CoverageAnalysis {
    cve_ageb: string;
    up_net: number;
    down_net: number;
    flujo: number;
    aforo: number;
    horas_pico?: { hora: string; aforo: number }[];
  }
  
  interface ApiResponse<T> {
    status: string;
    data: T;
    message?: string;
  }
  
  // Configuración de endpoints
  export const config = {
    endpoints: {
      stops: '/api/debug/paradas',
      routes: '/api/rutas',
      alternativeRoutes: '/api/rutas/alternativas',
      coverage: '/api/cobertura',
      stats: '/api/debug/stats',
    }
  };
  
  // API Service
  export const transportAPI = {
    // Obtener paradas
    getStops: async (): Promise<ApiResponse<{ sample_stops: Stop[] }>> => {
      try {
        const response = await fetch(config.endpoints.stops);
        if (!response.ok) {
          throw new Error('Error al obtener paradas');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching stops:', error);
        throw error;
      }
    },
  
    // Obtener rutas
    getRoutes: async (): Promise<ApiResponse<{ routes: Route[] }>> => {
      try {
        const response = await fetch(config.endpoints.routes);
        if (!response.ok) {
          throw new Error('Error al obtener rutas');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching routes:', error);
        throw error;
      }
    },
  
    // Obtener rutas alternativas
    getAlternativeRoutes: async (origen: string, destino: string): Promise<ApiResponse<{ alternatives: AlternativeRoute[] }>> => {
      try {
        const response = await fetch(
          `${config.endpoints.alternativeRoutes}?origen=${origen}&destino=${destino}`
        );
        if (!response.ok) {
          throw new Error('Error al obtener rutas alternativas');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching alternative routes:', error);
        throw error;
      }
    },
  
    // Obtener análisis de cobertura
    getCoverageAnalysis: async (ageb: string): Promise<ApiResponse<{ analysis: CoverageAnalysis }>> => {
      try {
        const response = await fetch(`${config.endpoints.coverage}/${ageb}`);
        if (!response.ok) {
          throw new Error('Error al obtener análisis de cobertura');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching coverage analysis:', error);
        throw error;
      }
    },
  
    // Obtener estadísticas del sistema
    getSystemStats: async (): Promise<ApiResponse<{
      total_agebs: number;
      total_paradas: number;
      total_rutas: number;
      aforo_total: number;
      top_agebs_por_aforo: Array<{ ageb: string; aforo_promedio: number }>;
    }>> => {
      try {
        const response = await fetch(config.endpoints.stats);
        if (!response.ok) {
          throw new Error('Error al obtener estadísticas del sistema');
        }
        return await response.json();
      } catch (error) {
        console.error('Error fetching system stats:', error);
        throw error;
      }
    },
  
    // Conexión WebSocket
    connectToWebSocket: () => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsURL = `${protocol}//${window.location.host}/ws/va-y-ven`;
      
      const ws = new WebSocket(wsURL);
      
      ws.onopen = () => {
        console.log('WebSocket Connected');
      };
  
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
  
      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };
  
      return ws;
    }
  };
  
  // Exportar por defecto
  export default transportAPI;