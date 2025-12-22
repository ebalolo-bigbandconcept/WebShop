import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import Modal from "../components/Modal";
import { useToast } from "../components/Toast";

function ListeClients() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const [clients, setclients] = useState();
  const [prenom, setFirstName] = useState("");
  const [nom, setLastName] = useState("");
  const [rue, setRue] = useState("");
  const [code_postal, setCodePostal] = useState("");
  const [ville, setVille] = useState("");
  const [tel, setTel] = useState("");
  const [email, setEmail] = useState("");

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setFirstNameError] = useState("");
  const [nom_error, setLastNameError] = useState("");
  const [rue_error, setRueError] = useState("");
  const [code_postal_error, setCodePostalError] = useState("");
  const [ville_error, setVilleError] = useState("");
  const [tel_error, setTelError] = useState("");
  const [email_error, setEmailError] = useState("");

  const [modeFORCE, setModeFORCE] = useState(false);

  const { showToast } = useToast();

  // Filter state
  const [filteredClients, setFilteredClients] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [caduqueFilter, setCaduqueFilter] = useState("active");

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10); // Items to display per page
  const [paginatedClients, setPaginatedClients] = useState([]);

  const modalRef = useRef(null);
  const showModal = () => {
    modalRef.current && modalRef.current.open();
  };


  // Automatically format French phone number as "01 23 45 67 89"
  const formatFrenchTel = (value) => {
    // Keep only digits
    const digits = value.replace(/\D/g, "").slice(0, 10);
    // Add spaces every 2 digits
    return digits.replace(/(\d{2})(?=\d)/g, "$1 ").trim();
  };

  // ### User input verifications ###
  const firstNameVerif = (value) => {
    if (value === "") {
      setFirstNameError("Veuillez entrer un prénom");
      return false;
    }
    setFirstNameError("");
    return true;
  };

  const lastNameVerif = (value) => {
    if (value === "") {
      setLastNameError("Veuillez entrer un nom");
      return false;
    }
    setLastNameError("");
    return true;
  };

  const rueVerif = (value) => {
    if (value === "") {
      setRueError("Veuillez entrer une adresse");
      return false;
    }
    setRueError("");
    return true;
  };

  const villeVerif = (value) => {
    if (value === "") {
      setVilleError("Veuillez entrer une commune");
      return false;
    }
    setVilleError("");
    return true;
  };

  const postalCodeVerif = (value) => {
    if (value === "") {
      setCodePostalError("Veuillez entrer un code postal");
      return false;
    }
    const postalCodeRegex = /^\d{5}$/;
    if (!postalCodeRegex.test(value)) {
      setCodePostalError("Format du code postal invalide");
      return false;
    }
    setCodePostalError("");
    return true;
  };

  const emailVerif = (value) => {
    if (value === "") {
      setEmailError("Veuillez entrer un email");
      return false;
    }
    const emailRegex = /[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      setEmailError("Format d'email invalide");
      return false;
    }
    setEmailError("");
    return true;
  };

  const telVerif = (value) => {
    if (value === "") {
      setTelError("Veuillez entrer un email");
      return false;
    }
    const telRegex = /^0[1-9](?:\s\d{2}){4}$/;
    if (!telRegex.test(value)) {
      setTelError("Format du numéro de téléphone invalide");
      return false;
    }
    setTelError("");
    return true;
  };

  // ### Fetch all clients from the backend ###
  const getAllUsersInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/clients/all`)
      .then((resp) => {
        setclients(resp.data);
        setFilteredClients(resp.data.data || []);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error !== "Aucun clients trouvé") {
            showToast({ message: error.response.data.error, variant: "danger" });
          } else {
            setclients({ data: [] }); // Ensure clients.data is not undefined
            setFilteredClients([]);
          }
        } else {
          showToast({ message: "Une erreur est survenue.", variant: "danger" });
        }
      });
  };

  // ### Add a new client to the database ###
  const addNewClient = async (e, forceValue = false) => {
    e.preventDefault();
    setFormSubmited(true);

    const isFirstNameValid = firstNameVerif(prenom);
    const isLastNameValid = lastNameVerif(nom);
    const isRueValid = rueVerif(rue);
    const isVilleValid = villeVerif(ville);
    const isCodePostalValid = postalCodeVerif(code_postal);
    const isEmailValid = emailVerif(email);
    const isTelValid = telVerif(tel);

    const isFormValid = isFirstNameValid && isLastNameValid && isEmailValid && isRueValid && isVilleValid && isCodePostalValid && isTelValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/clients/create`, {
          prenom: prenom,
          nom: nom,
          rue: rue,
          ville: ville,
          code_postal: code_postal,
          email: email,
          telephone: tel,
          force: forceValue,
        })
        .then((resp) => {
          console.log(resp);
          handleClose();
          showToast({ message: "Client créé avec succès", variant: "success" });
          getAllUsersInfo();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.status === 409 && !forceValue){
              handleForce();
            }else{
              showToast({ message: error.response.data.error, variant: "danger" });
            }
          } else {
            showToast({ message: "Une erreur est survenue.", variant: "danger" });
          }
        });
    }
  };

  const forceCreate = async () => {
    const fakeEvent = { preventDefault: () => {} };
    await addNewClient(fakeEvent, true);  // <-- force=true
    handleClose();
  }

  // ### Handle modal ###
  const handleForce = () => {
    setModeFORCE(true);
    showModal();
  }

  const handleOpenCreate = () => {
    setModeFORCE(false);
    setFormSubmited(false);
    setFirstNameError("");
    setLastNameError("");
    setEmailError("");
    setRueError("");
    setVilleError("");
    setCodePostalError("");
    setTelError("");
    showModal();
  };

  const handleClose = () => {
    modalRef.current && modalRef.current.close();
    // Reset form
    setFirstName("");
    setLastName("");
    setEmail("");
    setRue("");
    setVille("");
    setCodePostal("");
    setTel("");
    setFormSubmited(false);
    setFirstNameError("");
    setLastNameError("");
    setEmailError("");
    setRueError("");
    setVilleError("");
    setCodePostalError("");
    setTelError("");
    setModeFORCE(false);
  };

  useEffect(() => {
    getAllUsersInfo();
    setLoading(false);
  }, []);

  // ### Filter logic ###
  useEffect(() => {
    if (clients && clients.data) {
      let currentClients = clients.data;

      // Search term filter
      if (searchTerm) {
        currentClients = currentClients.filter(client =>
          client.nom.toLowerCase().includes(searchTerm.toLowerCase()) ||
          client.prenom.toLowerCase().includes(searchTerm.toLowerCase()) ||
          client.email.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }

      // Caduque filter
      if (caduqueFilter === 'caduque') {
        currentClients = currentClients.filter(client => client.caduque);
      } else if (caduqueFilter === 'active') {
        currentClients = currentClients.filter(client => !client.caduque);
      }

      setFilteredClients(currentClients);
      setCurrentPage(1); // Reset to first page on new filter
    }
  }, [clients, searchTerm, caduqueFilter]);

  // ### Pagination Logic ###
  useEffect(() => {
    if (filteredClients) {
      const startIndex = (currentPage - 1) * itemsPerPage;
      const endIndex = startIndex + itemsPerPage;
      setPaginatedClients(filteredClients.slice(startIndex, endIndex));
    }
  }, [filteredClients, currentPage, itemsPerPage]);

  // Reset to page 1 when itemsPerPage changes
  useEffect(() => {
    setCurrentPage(1);
  }, [itemsPerPage]);

  const modalTitle = modeFORCE ? 'Attention' : 'Ajouter un nouveau client';

  const modalBody = modeFORCE ? (
    "Un utilisateur à déja cet adresse email. Êtes vous sur de vouloir créer un client avec la même adresse mail ?"
  ) : (
    <form className="row">
      <div className="form-outline col-6">
        <label className="form-label">Nom</label>
        <input
          type="text"
          id="nom"
          value={nom}
          onChange={(e) => { setLastName(e.target.value); lastNameVerif(e.target.value); }}
          className={`form-control form-control-lg ${nom_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Entrer un nom"
        />
        <div className="invalid-feedback">{nom_error}</div>
      </div>
      <div className="form-outline col-6">
        <label className="form-label">Prénom</label>
        <input
          type="text"
          id="prénom"
          value={prenom}
          onChange={(e) => { setFirstName(e.target.value); firstNameVerif(e.target.value); }}
          className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Entrer un prénom"
        />
        <div className="invalid-feedback">{first_name_error}</div>
      </div>
      <div className="form-outline mt-4">
        <label className="form-label">Adresse</label>
        <input
          type="text"
          id="adresse"
          value={rue}
          onChange={(e) => { setRue(e.target.value); rueVerif(e.target.value); }}
          className={`form-control form-control-lg ${rue_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="2 Av. Gustave Eiffel"
        />
        <div className="invalid-feedback">{rue_error}</div>
      </div>
      <div className="form-outline col-6 mt-4">
        <label className="form-label">Ville</label>
        <input
          type="text"
          id="ville"
          value={ville}
          onChange={(e) => { setVille(e.target.value); villeVerif(e.target.value); }}
          className={`form-control form-control-lg ${ville_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Paris"
        />
        <div className="invalid-feedback">{ville_error}</div>
      </div>
      <div className="form-outline col-6 mt-4">
        <label className="form-label">Code postal</label>
        <input
          type="text"
          id="code_postal"
          value={code_postal}
          onChange={(e) => { setCodePostal(e.target.value); postalCodeVerif(e.target.value); }}
          className={`form-control form-control-lg ${code_postal_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="75007"
        />
        <div className="invalid-feedback">{code_postal_error}</div>
      </div>
      <div className="form-outline col-6 mt-4">
        <label className="form-label">Adresse mail</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => { setEmail(e.target.value); emailVerif(e.target.value); }}
          className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="Entrer une adresse mail"
        />
        <div className="invalid-feedback">{email_error}</div>
      </div>
      <div className="form-outline col-6 mt-4">
        <label className="form-label">Numéro de téléphone</label>
        <input
          type="tel"
          id="tel"
          value={tel}
          onChange={(e) => {
            const formatted = formatFrenchTel(e.target.value);
            setTel(formatted);
            telVerif(formatted);
          }}
          className={`form-control form-control-lg ${tel_error ? "is-invalid" : form_submited ? "is-valid" : ""}`}
          placeholder="01 23 45 67 89"
          maxLength={14}
        />
        <div className="invalid-feedback">{tel_error}</div>
      </div>
    </form>
  );

  const modalFooter = modeFORCE ? (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Non</button>
      <button className="btn btn-lg btn-success" onClick={forceCreate}>Oui</button>
    </div>
  ) : (
    <div className="d-flex justify-content-between w-100">
      <button className="btn btn-lg btn-danger" onClick={handleClose}>Annuler</button>
      <button className="btn btn-lg btn-success" onClick={addNewClient}>Enregistrer</button>
    </div>
  );


  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Liste des Clients</h1>
      <br/>
      <Modal ref={modalRef} title={modalTitle} footer={modalFooter} size="modal-xl" backdrop="static" keyboard={false}>
        {modalBody}
      </Modal>

      <div className="row mb-3 align-items-center">
        <div className="col-md-6">
          <input type="text" className="form-control form-control-lg" placeholder="Rechercher par nom, prénom, email..."
            value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)}/>
        </div>
        <div className="col-md-3">
          <select className="form-select form-select-lg" value={caduqueFilter} onChange={(e) => setCaduqueFilter(e.target.value)}>
            <option value="all">Tous les clients</option>
            <option value="caduque">Caduque</option>
            <option value="active">Actif</option>
          </select>
        </div>
        <div className="col-md-3">
            <div className="d-flex align-items-center justify-content-end">
                <label htmlFor="itemsPerPage" className="form-label me-2 mb-0">Clients par page:</label>
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
      <div className="w-100 d-flex justify-content-end">
        <button className="btn btn-lg btn-success mt-4" onClick={handleOpenCreate}>+ Ajouter un nouveau client</button>
      </div>
      <table className="table table-hover table-striped mt-4">
        <thead>
          <tr>
            <th scope="col">#</th>
            <th scope="col">Nom</th>
            <th scope="col">Prénom</th>
            <th scope="col">Adresse</th>
            <th scope="col">Numéro de téléphone</th>
            <th scope="col">Adresse email</th>
            <th scope="col">Caduque</th>
          </tr>
        </thead>
        <tbody>
          {paginatedClients.length > 0 ? (
            paginatedClients.map((client) => (
              <tr key={client.id} onClick={() => {navigate({ pathname: `/client/` + client.id });}}>
                <td>{client.id}</td>
                <td>{client.nom}</td>
                <td>{client.prenom}</td>
                <td>{client.rue}, {client.code_postal} <br/> {client.ville}</td>
                <td>{client.telephone}</td>
                <td>{client.email}</td>
                <td><input type="checkbox" disabled checked={!!client.caduque} className="form-check-input" id="caduque"/></td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="7">Aucun client trouvé</td>
            </tr>
            )}
        </tbody>
      </table>
      
      {/* START: Pagination Controls */}
      {filteredClients.length > itemsPerPage && (
        <nav>
          <ul className="pagination justify-content-center">
            <li className={`page-item ${currentPage === 1 ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage - 1); }}>Précédent</a>
            </li>
            {Array.from({ length: Math.ceil(filteredClients.length / itemsPerPage) }, (_, i) => i + 1).map(number => (
              <li key={number} className={`page-item ${currentPage === number ? 'active' : ''}`}>
                <a onClick={(e) => { e.preventDefault(); setCurrentPage(number); }} href="!#" className='page-link'>
                  {number}
                </a>
              </li>
            ))}
            <li className={`page-item ${currentPage >= Math.ceil(filteredClients.length / itemsPerPage) ? 'disabled' : ''}`}>
              <a className="page-link" href="!#" onClick={(e) => { e.preventDefault(); setCurrentPage(currentPage + 1); }}>Suivant</a>
            </li>
          </ul>
        </nav>
      )}
      {/* END: Pagination Controls */}
    </div>
  );
}
export default ListeClients;