requirejs.config({
    baseUrl: '/static/pdk/js/lib',
    paths: {
        app: '../app'
    },
    shim: {
        "jquery": {
            exports: "$"
        },
        "bootstrap": {
            deps: ['jquery', 'jquery-cookie'],
            exports: 'bootstrap'
        },
        "bootstrap-typeahead": {
            deps: ['bootstrap'],
        },
        "bootstrap-table": {
            deps: ['bootstrap'],
        }
    }
});
