import TransportMap from './components/TransportMap';

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      <div className="container mx-auto py-8 px-4">
        <h1 className="text-4xl font-bold mb-8 text-gray-900">
          Sistema Va y Ven
        </h1>
        <TransportMap />
      </div>
    </div>
  );
}

export default App;