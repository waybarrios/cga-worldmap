if (typeof OpenGeoportal == 'undefined') {
    OpenGeoportal = {};
} else if (typeof OpenGeoportal != "object") {
    throw new Error("OpenGeoportal already exists and is not an object");
}
if (typeof OpenGeoportal.Views == 'undefined') {
    OpenGeoportal.Views = {};
} else if (typeof OpenGeoportal.Views != "object") {
    throw new Error("OpenGeoportal.Views already exists and is not an object");
}
OpenGeoportal.Views.LeftPanel = Backbone.View.extend({
    initialize: function() {
        var mode = this.model.get("mode");
        this.listenTo(this.model, "change:mode", this.showPanel);
        var width = this.model.get("openWidth");
        var margin = width - jQuery("#roll_right").width();
        jQuery("#left_col").show().width(width).css({
	    "margin-left" : "-" + margin  + "px"
	});
        this.$rollRight = $("#roll_right");
        /*this.$leftCol = $("#left_col");
        var margin = width - this.$rollRight.width();
        this.$leftCol.show().width(width).css({
            "margin-left": "-" + margin + "px"
        });*/
    },
    events: {
        "click .arrow_right": "goRight",
        "click .arrow_left": "goLeft"
    },
    goRight: function() {
        var mode = this.model.get("mode");
        if (mode === "closed") {
            this.model.set({
                mode: "open"
            });
        } else if (mode === "open") {
            this.model.set({
                mode: "fullscreen"
            });
        }
    },
    goLeft: function() {
        var mode = this.model.get("mode");
        if (mode === "fullscreen") {
            this.model.set({
                mode: "open"
            });
        } else if (mode === "open") {
            this.model.set({
                mode: "closed"
            });
        }
    },
    setAlsoMoves: function() {
        if (!jQuery(".olControlPanel,.olControlModPanZoomBar,.olControlMousePosition,.googleLogo").hasClass("slideHorizontal")) {
            jQuery(".olControlPanel,.olControlModPanZoomBar,.olControlMousePosition,.googleLogo").addClass("slideHorizontal");
        }
    },
    showPanel: function() {
        this.setAlsoMoves();
        var mode = this.model.get("mode");
        if (mode === "open") {
            if (this.model.previous("mode") === "closed") {
                this.showPanelMidRight();
            } else {
                this.showPanelMidLeft();
            }
        } else if (mode === "closed") {
            this.showPanelClosed();
        } else if (mode === "fullscreen") {
            this.showPanelFullScreen();
        }
    },
    showPanelMidRight: function() {
        var $slide = jQuery(".slideHorizontal");
        if ($slide.is(":hidden")) {
            $slide.not(".corner").show();
        }
        if (this.$rollRight.is(":visible")) {
            this.$rollRight.hide();
        }
        var panelWidth = this.model.get("openWidth");
        var panelOffset = panelWidth - this.$rollRight.width();
        this.$el.show().width(panelWidth).css({
            "margin-left": -1 * panelOffset
        });
        var that = this;
        this.$el.add(".slideHorizontal").animate({
            'margin-left': '+=' + panelOffset
        }, {
            queue: false,
            duration: 500,
            complete: function() {
                $(this).trigger("adjustContents");
                that.resizablePanel();
                $(document).trigger("panelOpen");
            }
        });
        try {
            this.$el.resizable("enable");
        } catch (e) {}
    },
    showPanelMidLeft: function() {
        var panelWidth = this.model.get("openWidth");
        var panelOffset = panelWidth - this.$rollRight.width();
        var that = this;
        this.$el.show().animate({
            width: panelWidth
        }, {
            queue: false,
            duration: 500,
            complete: function() {
                $(".slideHorizontal").css({
                    'margin-left': panelOffset
                }).not(".corner").fadeIn();
                $(this).trigger("adjustContents");
                that.resizablePanel();
            }
        });
    },
    showPanelClosed: function() {
        var $slide = $(".slideHorizontal");

        if ($slide.is(":hidden")) {
            $slide.not(".corner").show();
        }
        var panelWidth = this.model.get("openWidth");
        var panelOffset = panelWidth - this.$rollRight.width();
        this.$el.add(".slideHorizontal").animate({
            'margin-left': '-=' + panelOffset
        }, {
            queue: false,
            duration: 500,
            complete: function() {
                $("#roll_right").show();
            }
        });
        this.$el.resizable("enable");
    },
    showPanelFullScreen: function() {
        if (this.$rollRight.is(":visible")) {
            this.$rollRight.hide();
        }
        if (this.$el.is(":hidden")) {
            this.$el.show();
        }
        $(".slideHorizontal").fadeOut();
        this.$el.animate({
            'width': $('#container').width()
        }, {
            queue: false,
            duration: 500,
            complete: function() {
                $(this).trigger("adjustContents");
            }
        });
    },
    resizablePanel: function() {
        this.setAlsoMoves();
        var that = this;
        this.$el.resizable({
            handles: 'se',
            start: function(event, ui) {
                $(document).trigger('eventMaskOn');
                this.$slide = $(".slideHorizontal");
                var margin = parseInt(this.$slide.css("margin-left"));
                that.model.set({
                    alsoMovesMargin: margin
                });
                this.prevWidth = ui.originalSize.width;
                ui.element.resizable("option", "minWidth", that.model.get("panelMinWidth"));
                var maxWidth = $("#container").width() - that.model.get("mapMinWidth");
                ui.element.resizable("option", "maxWidth", maxWidth);
            },
            prevWidth: null,
            resize: function(event, ui) {
                var delta = ui.size.width - this.prevWidth;
                this.prevWidth = ui.size.width;
                this.$slide.css({
                    "margin-left": "+=" + delta
                });
                $(this).trigger("panelResizing");
            },
            stop: function(event, ui) {
                $(document).trigger('eventMaskOff');
                var newWidth = ui.size.width;
                that.model.set({
                    openWidth: newWidth
                });
                $(this).trigger("adjustContents");
                if (Math.abs(ui.originalSize.width - newWidth) > ui.originalSize.width * .1) {
                    $(document).trigger("fireSearch");
                }
            }
        });
    }
});
