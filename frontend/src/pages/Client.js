import { useParams } from "react-router";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function Client() {
  const client_id = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const [client, setClient] = useState("");
  const [devis, setDevis] = useState([]);

  const [new_prenom, setNewPrenom] = useState("");
  const [new_nom, setNewNom] = useState("");
  const [new_rue, setNewRue] = useState("");
  const [new_code_postal, setNewCodePostal] = useState("");
  const [new_ville, setNewVille] = useState("");
  const [new_tel, setNewTel] = useState("");
  const [new_email, setNewEmail] = useState("");
  const [new_caduque, setNewCaduque] = useState("");

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setPrenomError] = useState("");
  const [nom_error, setNomError] = useState("");
  const [rue_error, setRueError] = useState("");
  const [code_postal_error, setCodePostalError] = useState("");
  const [ville_error, setVilleError] = useState("");
  const [tel_error, setTelError] = useState("");
  const [email_error, setEmailError] = useState("");

  const [force, setForce] = useState(false);

  // Automatically format French phone number as "01 23 45 67 89"
  const formatFrenchTel = (value) => {
    // Keep only digits
    const digits = value.replace(/\D/g, "").slice(0, 10);
    // Add spaces every 2 digits
    return digits.replace(/(\d{2})(?=\d)/g, "$1 ").trim();
  };

  // ### User input verifications ###
  const prenomVerif = (value) => {
    if (value === "") {
      setPrenomError("Veuillez entrer un prénom");
      return false;
    }
    setPrenomError("");
    return true;
  };

  const nomVerif = (value) => {
    if (value === "") {
      setNomError("Veuillez entrer un nom");
      return false;
    }
    setNomError("");
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

  const codePostalVerif = (value) => {
    if (value === "") {
      setCodePostalError("Veuillez entrer un code postal");
      return false;
    }
    const codePostalRegex = /^\d{5}$/;
    if (!codePostalRegex.test(value)) {
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
      setTelError("Veuillez entrer un numéro de téléphone");
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

  // ### handle modal ###
  const showModal = () => {
    const popup = document.getElementById("popup");
    const modal = new bootstrap.Modal(popup, {});
    modal.show();
  }

  const handleForce = () => {
    showModal();
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

    setForce(false)
  }

  // ### Force the update if user wants duplicate email
  const forceUpdate = async () => {
    setForce(true);
    await modifyClient();
    handleClose();
  }

  // ### Modify the user ###
  const modifyClient = async () => {
    setFormSubmited(true);

    const isNomValid = nomVerif(new_nom)
    const isPrenomValid = nomVerif(new_prenom)
    const isRueValid = nomVerif(new_rue)
    const isVilleValid = nomVerif(new_ville)
    const isCodePostalValid = nomVerif(new_code_postal)
    const isEmailValid = nomVerif(new_email)
    const isTelValid = nomVerif(new_tel)

    const isFormValid = isNomValid && isPrenomValid && isRueValid && isVilleValid && isCodePostalValid && isEmailValid && isTelValid;
    if (isFormValid) {
      const payload = {
        prenom: new_prenom,
        nom: new_nom,
        rue: new_rue,
        ville: new_ville,
        code_postal: new_code_postal,
        email: new_email,
        telephone: new_tel,
        caduque: new_caduque === "on" || new_caduque === true, // convert checkbox value
        force: force,
      };

      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/clients/update/${client.id}`, payload, {
          headers: {"Content-Type": "application/json"},
        })
        .then((resp) => {
          console.log(resp.data);
          alert("Les modifications ont bien été enregistrer.")
          getClientInfo();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            if (error.response.status === 409){
              handleForce();
            }
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  }

  const handleNewDevis = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/new-id`)
      .then((resp) => {
        navigate({ pathname: `/devis/${client.id}/${resp.data.id}` });
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  }

  const getClientAllDevis = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/devis/client/${client_id.id}`)
      .then((resp) => {
        setDevis(resp.data.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          if (error.response.data.error !== "Aucuns devis trouvé") {
            alert(error.response.data.error);
          }
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  const getClientInfo = async () => {
    httpClient
      .get(`${process.env.REACT_APP_BACKEND_URL}/clients/info/${client_id.id}`)
      .then((resp) => {
        setClient(resp.data);
      })
      .catch((error) => {
        if (error.response && error.response.data && error.response.data.error) {
          alert(error.response.data.error);
        } else {
          alert("Une erreur est survenue.");
        }
      });
  };

  // ### Fetch client all devis and info on page load ###
  useEffect(() => {
    getClientInfo();
    getClientAllDevis();
    setLoading(false);
    }, []);

  useEffect(() => {
    setNewPrenom(client.prenom);
    setNewNom(client.nom);
    setNewRue(client.rue);
    setNewCodePostal(client.code_postal);
    setNewVille(client.ville);
    setNewTel(client.telephone);
    setNewEmail(client.email);
    setNewCaduque(client.caduque);
  }, [client])
  
  if (loading) return <div>Chargement...</div>;

  return (
    <div>
      <div>
        <div className="d-flex justify-content-between align-items-center">
          <h1 className="col-lg-11 col-10">Client - {client.nom} {client.prenom}</h1>
          <button className="btn btn-danger col-lg-1 col-2" onClick={() => navigate('/liste-clients')}>Retour</button>
        </div>
        <br/>
        <form className="row">
          <div className="form-outline col-6">
            <label className="form-label">Nom</label>
            <input type="text" id="nom" value={new_nom} onChange={(e) => {setNewNom(e.target.value);nomVerif(e.target.value);}}
              className={`form-control form-control-lg ${nom_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nom"/>
            <div className="invalid-feedback">{nom_error}</div>
          </div>
          <div className="form-outline col-6">
            <label className="form-label">Prénom</label>
            <input type="text" id="prénom" value={new_prenom} onChange={(e) => {setNewPrenom(e.target.value);prenomVerif(e.target.value);}}
              className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un prénom"/>
            <div className="invalid-feedback">{first_name_error}</div>
          </div>
          <div className="form-outline mt-4">
            <label className="form-label">Adresse</label>
            <input type="text" id="adresse" value={new_rue} onChange={(e) => {setNewRue(e.target.value);rueVerif(e.target.value);}}
              className={`form-control form-control-lg ${rue_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="2 Av. Gustave Eiffel"/>
            <div className="invalid-feedback">{rue_error}</div>
          </div>
          <div className="form-outline col-6 mt-4">
            <label className="form-label">Ville</label>
            <input type="text" id="ville" value={new_ville} onChange={(e) => {setNewVille(e.target.value);villeVerif(e.target.value);}}
              className={`form-control form-control-lg ${ville_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Paris"/>
            <div className="invalid-feedback">{ville_error}</div>
          </div>
          <div className="form-outline col-6 mt-4">
            <label className="form-label">Code postal</label>
            <input type="text" id="code_postal" value={new_code_postal} onChange={(e) => {setNewCodePostal(e.target.value);codePostalVerif(e.target.value);}}
              className={`form-control form-control-lg ${code_postal_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="75007"/>
            <div className="invalid-feedback">{code_postal_error}</div>
          </div>
          <div className="form-outline col-6 mt-4">
            <label className="form-label">Adresse mail</label>
            <input type="email" id="email" value={new_email} onChange={(e) => {setNewEmail(e.target.value);emailVerif(e.target.value);}}
              className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une adresse mail"/>
            <div className="invalid-feedback">{email_error}</div>
          </div>
          <div className="form-outline col-6 mt-4">
            <label className="form-label">Numéro de téléphone</label>
            <input type="tel" id="tel" value={new_tel} onChange={(e) => {
              const formatted = formatFrenchTel(e.target.value);setNewTel(formatted);telVerif(formatted);}}
              className={`form-control form-control-lg ${tel_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="01 23 45 67 89" maxLength={14}/>
            <div className="invalid-feedback">{tel_error}</div>
          </div>
          <div className="form-outline col-6 mt-4">
            <label className="form-check-label me-2">Caduque :</label>
            <input type="checkbox" value={client} onChange={(e) => {setNewCaduque(e.target.value)}} className="form-check-input" id="caduque"/>
          </div>
        </form>
        <div className="d-flex w-100 justify-content-end">
          <button className="btn btn-lg btn-success mt-4" onClick={modifyClient}>Modifier</button>
        </div>
        <br/>
        <h2>Devis</h2>
        <br/>
        <table className="table table-hover table-striped">
          <thead>
            <tr>
              <th scope="col">#</th>
              <th scope="col">Titre</th>
              <th scope="col">Description</th>
              <th scope="col">Date</th>
              <th scope="col">Montant HT</th>
              <th scope="col">Montant TVA</th>
              <th scope="col">Montant TTC</th>
              <th scope="col">Statut</th>
            </tr>
          </thead>
          <tbody>
            {devis.length > 0 ? (
              devis.map((devis) => (
                <tr key={devis.id} onClick={() => {navigate(`/devis/${client.id}/${devis.id}`, {state : {from: `/client/${client.id}`}});}}>
                  <td>{devis.id}</td>
                  <td>{devis.titre}</td>
                  <td>{devis.description}</td>
                  <td>{devis.date}</td>
                  <td>{devis.montant_HT} €</td>
                  <td>{devis.montant_TVA} €</td>
                  <td>{devis.montant_TTC} €</td>
                  <td>{devis.statut}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={8}>Aucun devis trouvé</td>
              </tr>
            )}
          </tbody>
        </table>
        <br/>
        <button className="btn btn-primary" onClick={() => handleNewDevis()}>+ Créer un devis</button>
      </div>
      <div className="modal fade" id="popup" tabIndex="-1">
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h1 className="modal-title fs-5" id="popupLabel">Attention</h1>
              </div>
              <div className="modal-body">
                <h5>Un client utilise déjà cet email, êtes vous sur de vouloir modifier le clients quand même ?</h5>
              </div>
              <div className="modal-footer d-flex justify-content-between">
                <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Non</button>
                <button className="btn btn-lg btn-success" onClick={forceUpdate}>Oui</button>
              </div>
            </div>
          </div>
        </div>
    </div>
  );
  }
export default Client;