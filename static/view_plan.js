window.onload = () => {
	const total_calories_breakfast = Number.parseFloat(
		document.getElementById("tot_calories_breakfast").innerHTML,
	);
	const total_calories_lunch = Number.parseFloat(
		document.getElementById("tot_calories_lunch").innerHTML,
	);
	const total_calories_dinner = Number.parseFloat(
		document.getElementById("tot_calories_dinner").innerHTML,
	);
	const total_calories_snack = Number.parseFloat(
		document.getElementById("tot_calories_snack").innerHTML,
	);
	const total_protein_breakfast = Number.parseFloat(
		document.getElementById("tot_protein_breakfast").innerHTML,
	);
	const total_carbs_breakfast = Number.parseFloat(
		document.getElementById("tot_carbohydrate_breakfast").innerHTML,
	);
	const total_fat_breakfast = Number.parseFloat(
		document.getElementById("tot_fat_breakfast").innerHTML,
	);
	const total_protein_lunch = Number.parseFloat(
		document.getElementById("tot_protein_lunch").innerHTML,
	);
	const total_carbs_lunch = Number.parseFloat(
		document.getElementById("tot_carbohydrate_lunch").innerHTML,
	);
	const total_fat_lunch = Number.parseFloat(
		document.getElementById("tot_fat_lunch").innerHTML,
	);
	const total_protein_dinner = Number.parseFloat(
		document.getElementById("tot_protein_dinner").innerHTML,
	);
	const total_carbs_dinner = Number.parseFloat(
		document.getElementById("tot_carbohydrate_dinner").innerHTML,
	);
	const total_fat_dinner = Number.parseFloat(
		document.getElementById("tot_fat_dinner").innerHTML,
	);
	const total_protein_snack = Number.parseFloat(
		document.getElementById("tot_protein_snack").innerHTML,
	);
	const total_carbs_snack = Number.parseFloat(
		document.getElementById("tot_carbohydrate_snack").innerHTML,
	);
	const total_fat_snack = Number.parseFloat(
		document.getElementById("tot_fat_snack").innerHTML,
	);

	const chart_breakfast = new CanvasJS.Chart("chart_doughnut_macro_breakfast", {
		title: {
			text: "Breakfast",
		},
		legend: {
			fontSize: 20,
			horizontalAlign: "left",
		},
		data: [
			{
				type: "doughnut",
				showInLegend: true,
				toolTipContent: "{name} - #percent%",
				startAngle: 0,
				indexLabel: "{y} g",
				dataPoints: [
					{
						y: total_protein_breakfast,
						name: "protein",
						indexLabelFontSize: 15,
					},
					{ y: total_fat_breakfast, name: "fat", indexLabelFontSize: 15 },
					{ y: total_carbs_breakfast, name: "carbs", indexLabelFontSize: 15 },
				],
			},
		],
	});

	const chart_lunch = new CanvasJS.Chart("chart_doughnut_macro_lunch", {
		title: {
			text: "Lunch",
		},
		legend: {
			fontSize: 20,
			horizontalAlign: "left",
		},
		data: [
			{
				type: "doughnut",
				showInLegend: true,
				toolTipContent: "{name} - #percent%",
				startAngle: 0,
				indexLabel: "{y} g",
				dataPoints: [
					{ y: total_protein_lunch, name: "protein", indexLabelFontSize: 15 },
					{ y: total_fat_lunch, name: "fat", indexLabelFontSize: 15 },
					{ y: total_carbs_lunch, name: "carbs", indexLabelFontSize: 15 },
				],
			},
		],
	});

	const chart_dinner = new CanvasJS.Chart("chart_doughnut_macro_dinner", {
		title: {
			text: "Dinner",
		},
		legend: {
			fontSize: 20,
			horizontalAlign: "left",
		},
		data: [
			{
				type: "doughnut",
				showInLegend: true,
				toolTipContent: "{name} - #percent%",
				startAngle: 0,
				indexLabel: "{y} g",
				dataPoints: [
					{ y: total_protein_dinner, name: "protein", indexLabelFontSize: 15 },
					{ y: total_fat_dinner, name: "fat", indexLabelFontSize: 15 },
					{ y: total_carbs_dinner, name: "carbs", indexLabelFontSize: 15 },
				],
			},
		],
	});

	const chart_snack = new CanvasJS.Chart("chart_doughnut_macro_snack", {
		title: {
			text: "Snacks",
		},
		legend: {
			fontSize: 20,
			horizontalAlign: "left",
		},
		data: [
			{
				type: "doughnut",
				showInLegend: true,
				toolTipContent: "{name} - #percent%",
				startAngle: 50,
				indexLabel: "{y} g",
				dataPoints: [
					{ y: total_protein_snack, name: "protein", indexLabelFontSize: 15 },
					{ y: total_fat_snack, name: "fat", indexLabelFontSize: 15 },
					{ y: total_carbs_snack, name: "carbs", indexLabelFontSize: 15 },
				],
			},
		],
	});

	const chart_calories = new CanvasJS.Chart("chart_calories", {
		title: {
			text: "Calories Distribution",
		},
		axisY: {
			title: "Kcal",
		},
		data: [
			{
				toolTipContent: "{label} - {y}Kcal",
				dataPoints: [
					{ x: 1, y: total_calories_breakfast, label: "Breakfast" },
					{ x: 2, y: total_calories_lunch, label: "Lunch" },
					{ x: 3, y: total_calories_dinner, label: "Dinner" },
					{ x: 4, y: total_calories_snack, label: "Snacks" },
				],
			},
		],
	});

	const chart_protein = new CanvasJS.Chart("chart_protein", {
		title: {
			text: "Protein Distribution",
		},
		axisY: {
			title: "grams",
		},
		data: [
			{
				toolTipContent: "{label} - {y}g",
				dataPoints: [
					{ x: 1, y: total_protein_breakfast, label: "Breakfast" },
					{ x: 2, y: total_protein_lunch, label: "Lunch" },
					{ x: 3, y: total_protein_dinner, label: "Dinner" },
					{ x: 4, y: total_protein_snack, label: "Snacks" },
				],
			},
		],
	});

	const chart_carbs = new CanvasJS.Chart("chart_carbs", {
		title: {
			text: "Carbohydrate Distribution",
		},
		axisY: {
			title: "grams",
		},
		data: [
			{
				toolTipContent: "{label} - {y}g",
				dataPoints: [
					{ x: 1, y: total_carbs_breakfast, label: "Breakfast" },
					{ x: 2, y: total_carbs_lunch, label: "Lunch" },
					{ x: 3, y: total_carbs_dinner, label: "Dinner" },
					{ x: 4, y: total_carbs_snack, label: "Snacks" },
				],
			},
		],
	});

	const chart_fat = new CanvasJS.Chart("chart_fat", {
		title: {
			text: "Fat Distribution",
		},
		axisY: {
			title: "grams",
		},
		data: [
			{
				toolTipContent: "{label} - {y}g",
				dataPoints: [
					{ x: 1, y: total_fat_breakfast, label: "Breakfast" },
					{ x: 2, y: total_fat_lunch, label: "Lunch" },
					{ x: 3, y: total_fat_dinner, label: "Dinner" },
					{ x: 4, y: total_fat_snack, label: "Snacks" },
				],
			},
		],
	});

	default_text(
		chart_breakfast,
		"Add some ingredients to see your macros here!",
	);
	default_text(chart_lunch, "Add some ingredients to see your macros here!");
	default_text(chart_dinner, "Add some ingredients to see your macros here!");
	default_text(chart_snack, "Add some ingredients to see your macros here!");
	default_text(chart_calories, "Add some ingredients to see your macros here!");
	default_text(chart_protein, "Add some ingredients to see your macros here!");
	default_text(chart_carbs, "Add some ingredients to see your macros here!");
	default_text(chart_fat, "Add some ingredients to see your macros here!");
	chart_calories.render();
	chart_protein.render();
	chart_carbs.render();
	chart_fat.render();
	chart_breakfast.render();
	chart_lunch.render();
	chart_dinner.render();
	chart_snack.render();
};

function default_text(chart, text) {
	// Grab the dataPoints from the chart
	const { dataPoints } = chart.options.data[0];
	let empty = true;

	// Check if at least one point isn't 0
	for (let i = 0; i < dataPoints.length; i++) {
		if (dataPoints[i].y > 0) {
			empty = false;
			break;
		}
	}

	// We use subtitles to show a default text
	chart.options.subtitles = [];

	if (empty) {
		chart.options.subtitles.push({
			fontSize: 20,
			text: text,
			verticalAlign: "center",
		});
	}
}
