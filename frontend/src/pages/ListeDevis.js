import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";

function ListeDevis() {
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate();
  const [devis, setDevis] = useState([])

  // Filter and Pagination state
  const [filteredDevis, setFilteredDevis] = useState([]);
  const [paginatedDevis, setPaginatedDevis] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // ### Fetch all devis from all clients from the backend ###
  const getEveryDevis = async () => {
    try {
      const resp = await httpClient.get(`${process.env.REACT_APP_BACKEND_URL}/devis/all`);
      setDevis(resp.data.data || []);
      setFilteredDevis(resp.data.data || []);
    } catch (error) {
      if (error.response && error.response.data && error.response.data.error) {
        if (error.response.data.error !== "Aucuns devis trouvé") {
          alert(error.response.data.error);
        }
      } else {
        alert("Une erreur est survenue.");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getEveryDevis();
  }, []);

  // ### Filter logic ###
  useEffect(() => {
    let currentDevis = devis;

    // Search term filter
    if (searchTerm) {
      currentDevis = currentDevis.filter(d =>
        d.titre.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        `${d.client.prenom} ${d.client.nom}`.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      currentDevis = currentDevis.filter(d => d.statut === statusFilter);
    }

    setFilteredDevis(currentDevis);
    setCurrentPage(1);
  }, [devis, searchTerm, statusFilter]);

  // ### Pagination Logic ###
  useEffect(() => {
    if (filteredDevis) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      setPaginatedDevis(filteredDevis.slice(startIndex, endIndex));
    }
  }, [filteredDevis, currentPage, itemsPerPage]);

  // Reset to page 1 when itemsPerPage changes
  useEffect(() => {
    setCurrentPage(1);
  }, [itemsPerPage]);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Liste des devis</h1>
      
      <div className="row mb-3 align-items-center">
        <div className="col-md-6">
          <input type="text" className="form-control form-control-lg" placeholder="Rechercher par client, devis, description..."
            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}/>
        </div>
        <div className="col-md-3">
          <select className="form-select form-select-lg" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">Tous</option>
            <option value="Non payé">Non payé</option>
            <option value="Payé">Payé</option>
          </select>
        </div>
        <div className="col-md-3">
            <div className="d-flex align-items-center justify-content-end">
                <label htmlFor="itemsPerPage" className="form-label me-2 mb-0">Par page:</label>
                <select id="itemsPerPage" className="form-select form-select-lg w-auto" value={itemsPerPage}
                    onChange={(e) => setItemsPerPage(Number(e.target.value))}>
                    <option value={10}>10</option>
                    <option value={25}>25</option>
                    <option value={50}>50</option>
                    <option value={100}>100</option>
                </select>
            </div>
        </div>
      </div>

      <table className="table table-hover table-striped">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Client</th>
            <th scope="col">Devis</th>
            <th scope="col">Description</th>
            <th scope="col">Date</th>
            <th scope="col">Montant HT</th>
            <th scope="col">Montat TVA</th>
            <th scope="col">Montant TTC</th>
            <th scope="col">Statut</th>
          </tr>
        </thead>
        <tbody>
          {paginatedDevis.length > 0 ? (
            paginatedDevis.map((d) => (
              <tr key={d.id} onClick={() => {navigate(`/devis/${d.client.id}/${d.id}`, {state : {from: '/liste-devis'}});}}>
                <td>{d.id}</td>
                <td>{d.client.nom} {d.client.prenom}</td>
                <td>{d.titre}</td>
                <td>{d.description}</td>
                <td>{d.date}</td>
                <td>{d.montant_HT} €</td>
                <td>{d.montant_TVA} €</td>
                <td>{d.montant_TTC} €</td>
                <td>{d.statut}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="9">Aucun devis trouvé</td>
            </tr>
            )}
        </tbody>
      </table>

      {filteredDevis.length > itemsPerPage && (
        <nav>
          <ul className="pagination justify-content-center">
            <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage - 1); }}>
                Précédent
              </a>
            </li>
            {Array.from({ length: Math.ceil(filteredDevis.length / itemsPerPage) }, (_, i) => i + 1).map(number => (
              <li key={number} className={`page-item ${currentPage === number ? 'active' : ''}`}>
                <a onClick={(e) => { e.preventDefault(); setCurrentPage(number); }} href="!#" className='page-link'>
                  {number}
                </a>
              </li>
            ))}
            <li className={`page-item ${currentPage >= Math.ceil(filteredDevis.length / itemsPerPage) ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage + 1); }}>
                Suivant
              </a>
            </li>
          </ul>
        </nav>
      )}

    </div>
  );
}
export default ListeDevis;
