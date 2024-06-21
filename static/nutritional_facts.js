window.onload = () => {
	const total_protein = Number.parseFloat(
		document.getElementById("protein_value").innerHTML,
	);
	const total_carbs = Number.parseFloat(
		document.getElementById("carbohydrate_value").innerHTML,
	);
	const total_fat = Number.parseFloat(
		document.getElementById("fat_value").innerHTML,
	);

	const chart = new CanvasJS.Chart("chart_doughnut_macro", {
		title: {
			text: "Main macros relative distribution",
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
				dataPoints: [
					{ y: total_protein, name: "protein" },
					{ y: total_fat, name: "fat" },
					{ y: total_carbs, name: "carbs" },
				],
			},
		],
	});

	chart.render();
};
