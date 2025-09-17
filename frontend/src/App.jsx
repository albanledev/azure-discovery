import { useState, useEffect } from "react";

function App() {
  const [email, setEmail] = useState("");
  const [connected, setConnected] = useState(false);
  const [hasVoted, setHasVoted] = useState(false);
  const [votes, setVotes] = useState([]);
  const [results, setResults] = useState(null);

  const API_URL = "https://bayrou-azure-functions.azurewebsites.net/api";

  const handleConnect = async () => {
    if (!email) {
      alert("Entre ton email !");
      return;
    }

    await fetch(`${API_URL}/user`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, pseudo: email }),
    });

    const res = await fetch(`${API_URL}/hasVoted?email=${encodeURIComponent(email)}`);
    const data = await res.json();
    setConnected(true);
    setHasVoted(data.hasVoted);
  };

  const handleVote = async (choice) => {
    if (!email) return;

    await fetch(`${API_URL}/vote`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, choice }),
    });

    setHasVoted(true);
    fetchVotes();
  };

  const fetchVotes = async () => {
    const res = await fetch(`${API_URL}/votes`);
    const data = await res.json();
    setVotes(data);
  };

  const fetchResults = async () => {
    const res = await fetch(`${API_URL}/results`);
    const data = await res.json();
    setResults(data);
  };

  useEffect(() => {
    fetchVotes();
    const interval = setInterval(fetchVotes, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ maxWidth: 600, margin: "auto", textAlign: "center" }}>
      <h1>Est-ce que François Bayrou nous manque ?</h1>

      {!connected ? (
        <div>
          <input
            type="email"
            placeholder="Entre ton email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
          <button onClick={handleConnect}>Se connecter</button>
        </div>
      ) : (
        <div>
          <p>Email connecté : {email}</p>
          {hasVoted ? (
            <p style={{ color: "red" }}>Tu as déjà voté.</p>
          ) : (
            <div>
              <button onClick={() => handleVote("Oui")}>Oui</button>
              <button onClick={() => handleVote("Non")}>Non</button>
            </div>
          )}
        </div>
      )}

      <h2>Résultats détaillés</h2>
      <ul>
        {votes.map((v, idx) => (
          <li key={idx}>
            {v.pseudo || v.email} : {v.choice}
          </li>
        ))}
      </ul>

      <h2>Total</h2>
      <button onClick={fetchResults}>Voir le résultat</button>

      {results && (
        <div style={{ marginTop: 20 }}>
          <h1 style={{ color: "green", fontSize: "2em" }}>Oui : {results.Oui}</h1>
          <h1 style={{ color: "red", fontSize: "2em" }}>Non : {results.Non}</h1>
        </div>
      )}
    </div>
  );
}

export default App;
