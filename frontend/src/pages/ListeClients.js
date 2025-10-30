import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import httpClient from "../components/httpClient";
import bootstrap from "bootstrap/dist/js/bootstrap.js";

function ListeClients() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);

  const [clients, setclients] = useState();
  const [new_prenom, setNewFirstName] = useState("");
  const [new_nom, setNewLastName] = useState("");
  const [new_street, setNewStreet] = useState("");
  const [new_postal_code, setNewPostalCode] = useState("");
  const [new_city, setNewCity] = useState("");
  const [new_phone, setNewPhone] = useState("");
  const [new_email, setNewEmail] = useState("");

  const [form_submited, setFormSubmited] = useState(false);
  const [first_name_error, setFirstNameError] = useState("");
  const [nom_error, setLastNameError] = useState("");
  const [street_error, setStreetError] = useState("");
  const [postal_code_error, setPostalCodeError] = useState("");
  const [city_error, setCityError] = useState("");
  const [phone_error, setPhoneError] = useState("");
  const [email_error, setEmailError] = useState("");

  // Automatically format French phone number as "01 23 45 67 89"
  const formatFrenchPhone = (value) => {
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

  const streetVerif = (value) => {
    if (value === "") {
      setStreetError("Veuillez entrer une adresse");
      return false;
    }
    setStreetError("");
    return true;
  };

  const cityVerif = (value) => {
    if (value === "") {
      setCityError("Veuillez entrer une commune");
      return false;
    }
    setCityError("");
    return true;
  };

  const postalCodeVerif = (value) => {
    if (value === "") {
      setPostalCodeError("Veuillez entrer un code postal");
      return false;
    }
    const postalCodeRegex = /^\d{5}$/;
    if (!postalCodeRegex.test(value)) {
      setPostalCodeError("Format du code postal invalide");
      return false;
    }
    setPostalCodeError("");
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

  const phoneVerif = (value) => {
    if (value === "") {
      setPhoneError("Veuillez entrer un email");
      return false;
    }
    const phoneRegex = /^0[1-9](?:\s\d{2}){4}$/;
    if (!phoneRegex.test(value)) {
      setPhoneError("Format du numéro de téléphone invalide");
      return false;
    }
    setPhoneError("");
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
  const addNewClient = async (e) => {
    e.preventDefault();
    setFormSubmited(true);

    const isFirstNameValid = firstNameVerif(new_prenom);
    const isLastNameValid = lastNameVerif(new_nom);
    const isStreetValid = streetVerif(new_street);
    const isCityValid = cityVerif(new_city);
    const isPostalCodeValid = postalCodeVerif(new_postal_code);
    const isEmailValid = emailVerif(new_email);
    const isPhoneValid = phoneVerif(new_phone);

    const isFormValid = isFirstNameValid && isLastNameValid && isEmailValid && isStreetValid && isCityValid && isPostalCodeValid && isPhoneValid;

    if (isFormValid) {
      httpClient
        .post(`${process.env.REACT_APP_BACKEND_URL}/clients/create`, {
          prenom: new_prenom,
          nom: new_nom,
          street: new_street,
          city: new_city,
          postal_code: new_postal_code,
          email: new_email,
          phone: new_phone,
        })
        .then((resp) => {
          console.log(resp);
          handleClose();
          getAllUsersInfo();
        })
        .catch((error) => {
          if (error.response && error.response.data && error.response.data.error) {
            alert(error.response.data.error);
          } else {
            alert("Une erreur est survenue.");
          }
        });
    }
  };

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
    setNewFirstName("");
    setNewLastName("");
    setNewEmail("");
    setNewStreet("");
    setNewCity("");
    setNewPostalCode("");
    setNewPhone("");
    setFormSubmited(false);
    setFirstNameError("");
    setLastNameError("");
    setEmailError("");
    setStreetError("");
    setCityError("");
    setPostalCodeError("");
    setPhoneError("");
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
        <div className="modal fade" id="popup" tabIndex="-1">
          <div className="modal-dialog modal-xl">
            <div className="modal-content">
              <div className="modal-header">
                <h1 className="modal-title fs-5" id="popupLabel">Ajouter un nouveau client.</h1>
              </div>
              <div className="modal-body">
                <form className="row">
                  <div className="form-outline col-6">
                    <label className="form-label">Nom</label>
                    <input type="text" id="nom" value={new_nom} onChange={(e) => {setNewLastName(e.target.value);lastNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${nom_error ? "is-invalid" : form_submited ? "is-valid": ""}`} placeholder="Entrer un nom."/>
                    <div className="invalid-feedback">{nom_error}</div>
                  </div>
                  <div className="form-outline col-6">
                    <label className="form-label">Prénom</label>
                    <input type="text" id="prénom" value={new_prenom} onChange={(e) => {setNewFirstName(e.target.value);firstNameVerif(e.target.value);}}
                      className={`form-control form-control-lg ${first_name_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer un prénom."/>
                    <div className="invalid-feedback">{first_name_error}</div>
                  </div>
                  <div className="form-outline mt-4">
                    <label className="form-label">Adresse</label>
                    <input type="text" id="adresse" value={new_street} onChange={(e) => {setNewStreet(e.target.value);streetVerif(e.target.value);}}
                      className={`form-control form-control-lg ${street_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="2 Av. Gustave Eiffel."/>
                    <div className="invalid-feedback">{street_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Ville</label>
                    <input type="text" id="ville" value={new_city} onChange={(e) => {setNewCity(e.target.value);cityVerif(e.target.value);}}
                      className={`form-control form-control-lg ${city_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Paris"/>
                    <div className="invalid-feedback">{city_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Code postal</label>
                    <input type="text" id="code_postal" value={new_postal_code} onChange={(e) => {setNewPostalCode(e.target.value);postalCodeVerif(e.target.value);}}
                      className={`form-control form-control-lg ${postal_code_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="75007"/>
                    <div className="invalid-feedback">{postal_code_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Adresse mail</label>
                    <input type="email" id="email" value={new_email} onChange={(e) => {setNewEmail(e.target.value);emailVerif(e.target.value);}}
                      className={`form-control form-control-lg ${email_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="Entrer une adresse mail."/>
                    <div className="invalid-feedback">{email_error}</div>
                  </div>
                  <div className="form-outline col-6 mt-4">
                    <label className="form-label">Numéro de téléphone</label>
                    <input type="tel" id="tel" value={new_phone} onChange={(e) => {
                      const formatted = formatFrenchPhone(e.target.value);
                      setNewPhone(formatted);
                      phoneVerif(formatted);
                    }}className={`form-control form-control-lg ${phone_error ? "is-invalid" : form_submited ? "is-valid" : ""}`} placeholder="01 23 45 67 89" maxLength={14}/>
                    <div className="invalid-feedback">{phone_error}</div>
                  </div>
                </form>
              </div>
              <div className="modal-footer d-flex justify-content-between">
                <button className="btn btn-lg btn-danger" data-bs-dismiss="modal" onClick={handleClose}>Annuler</button>
                <button className="btn btn-lg btn-success" onClick={addNewClient}>Enregistrer</button>
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
