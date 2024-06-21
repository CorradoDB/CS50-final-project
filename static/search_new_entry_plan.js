window.onload = () => {
	const radio_to_check = document.getElementById("remember_radio").value;
	if (radio_to_check === "1") {
		document.getElementById("inline_radio_food").checked = true;
	} else if (radio_to_check === "2") {
		document.getElementById("inline_radio_recipe").checked = true;
	}
};
