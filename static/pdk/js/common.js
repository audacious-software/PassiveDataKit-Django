requirejs.config({
    baseUrl: "/static/pdk/js/lib",
    paths: {
        app: "../app"
    },
    shim: {
        "jquery": {
            exports: "$"
        },
        "moment": {
            exports: "moment"
        },
        "bootstrap": {
            deps: ["jquery", "jquery-cookie"],
            exports: "bootstrap"
        },
        "bootstrap-typeahead": {
            deps: ["bootstrap"],
        },
        "bootstrap-table": {
            deps: ["bootstrap"],
        },
        "bootstrap-datepicker": {
            deps: ["bootstrap"],
        },
        "bootstrap-timepicker": {
            deps: ["bootstrap"],
        },
        "rickshaw": {
            deps: ["d3-layout", "jquery"],
            exports: "Rickshaw"
        },
        "d3-layout": {
            deps: ["d3", "jquery"]
        },
        "d3": {
            exports: "d3"
        }
    }
});
