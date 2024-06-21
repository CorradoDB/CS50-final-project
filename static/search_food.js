function on_radio_change(value) {
	if (value === "no_brand") {
		document.getElementById("floating_brand").disabled = true;
	} else {
		document.getElementById("floating_brand").disabled = false;
	}
}

window.onload = () => {
	const radio_to_check = document.getElementById("remember_radio").value;
	if (radio_to_check === "1") {
		document.getElementById("inline_radio_all").checked = true;
	} else if (radio_to_check === "2") {
		document.getElementById("inline_radio_generic").checked = true;
		document.getElementById("floating_brand").disabled = true;
	} else if (radio_to_check === "3") {
		document.getElementById("inline_radio_branded").checked = true;
	}
};
