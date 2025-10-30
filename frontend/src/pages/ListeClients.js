import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

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
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
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
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error !== "Aucun clients trouvé") {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
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
          getAllUsersInfo();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.status === 409 && !forceValue){
              handleForce();
            }else{
              alert(error.response.data.error);
            }
          } else {
            alert("Une erreur est survenue.");
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
  }

  const handleClose = () => {
    // Close modal
    const popup = document.getElementById("popup");
    const modal = bootstrap.Modal.getInstance(popup);
    if (modal){
      modal.hide();
    }
    // Close modal residues
    const backdrops = document.querySelectorAll(".modal-backdrop");
    backdrops.forEach((b) => b.remove());

    document.body.classList.remove("modal-open");
    document.body.style.overflow = "";
    document.body.style.paddingRight = "";
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
  };

  useEffect(() => {
    getAllUsersInfo();
    setLoading(false);
  }, []);

  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <h1>Liste des Clients</h1>
      <br/>
      <div>
        <div className="modal fade" id="popup" tabIndex="-1" data-bs-backdrop="static" data-bs-keyboard="false">
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h1 className="modal-title fs-5" id="popupLabel">{modeFORCE ? 'Attention' : 'Ajouter un nouveau client'}</h1>
              </div>
              <div className="modal-body">
                {modeFORCE ? ("Un utilisateur à déja cet adresse email. Êtes vous sur de vouloir créer un client avec la même adresse mail ?") : (
                <form className="row">
                  <div className="form-outline col-6">
                    <label className="form-label">Nom</label>
                    <input type="text" id="nom" value={nom} onChange={(e) => {setLastName(e.target.value);lastNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${nom_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nom"/>
                    <div className="invalid-feedback">{nom_error}</div>
                  </div>
                  <div className="form-outline col-6">
                    <label className="form-label">Prénom</label>
                    <input type="text" id="prénom" value={prenom} onChange={(e) => {setFirstName(e.target.value);firstNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un prénom"/>
                    <div className="invalid-feedback">{first_name_error}</div>
                  </div>
                  <div className="form-outline mt-4">
                    <label className="form-label">Adresse</label>
                    <input type="text" id="adresse" value={rue} onChange={(e) => {setRue(e.target.value);rueVerif(e.target.value);}}
                      className={`form-control form-control-lg ${rue_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="2 Av. Gustave Eiffel"/>
                    <div className="invalid-feedback">{rue_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Ville</label>
                    <input type="text" id="ville" value={ville} onChange={(e) => {setVille(e.target.value);villeVerif(e.target.value);}}
                      className={`form-control form-control-lg ${ville_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Paris"/>
                    <div className="invalid-feedback">{ville_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Code postal</label>
                    <input type="text" id="code_postal" value={code_postal} onChange={(e) => {setCodePostal(e.target.value);postalCodeVerif(e.target.value);}}
                      className={`form-control form-control-lg ${code_postal_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="75007"/>
                    <div className="invalid-feedback">{code_postal_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Adresse mail</label>
                    <input type="email" id="email" value={email} onChange={(e) => {setEmail(e.target.value);emailVerif(e.target.value);}}
                      className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une adresse mail"/>
                    <div className="invalid-feedback">{email_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Numéro de téléphone</label>
                    <input type="tel" id="tel" value={tel} onChange={(e) => {
                      const formatted = formatFrenchTel(e.target.value);
                      setTel(formatted);
                      telVerif(formatted);
                    }}className={`form-control form-control-lg ${tel_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="01 23 45 67 89" maxLength={14}/>
                    <div className="invalid-feedback">{tel_error}</div>
                  </div>
                </form>
                )}
              </div>
              <div className="modal-footer ">
                {modeFORCE ? (
                    <div className="d-flex justify-content-between w-100">
                      <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Non</button>
                      <button className="btn btn-lg btn-success" onClick={forceCreate}>Oui</button>
                    </div>
                ) : (
                  <div className="d-flex justify-content-between w-100">
                    <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Annuler</button>
                    <button className="btn btn-lg btn-success" onClick={addNewClient}>Enregistrer</button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
      <table className="table table-hover table-striped">
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
          {clients !== undefined ? (
            clients.data.map((client) => (
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
              <td colSpan={6}>Aucun client trouvé</td>
            </tr>
            )}
        </tbody>
      </table>
      <br/>
      <button className="btn btn-primary" data-bs-toggle="modal" data-bs-target="#popup">+ Ajouter un nouveau client</button>
    </div>
  );
}
export default ListeClients;
