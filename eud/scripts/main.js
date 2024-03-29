define([
	'jquery', 
	'tag',
	'axios',
	'intro.min'
], function(
	$, 
	TAG,
	axios,
	introJs
) {

	function get_shifts(words1, words2) {
		var shifts = {};
		var pointer1 = 0;
		var pointer2 = 0;
		while (pointer1 < words1.length)
		{
			shifts[pointer2] = pointer1
			if (words1[pointer1].text == words2[pointer2].text)
			{
				pointer1++;
			}
			else
			{
				shifts[pointer2] -= 0.9
			}
			pointer2++;
		}
		return shifts
	}

	// -------------
	// Basic example
	// -------------
	function main() {
		
		function displayTree(data, containerId, category) {
			var links = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : [];
            const container = $('#' + containerId);
			const basicTag = TAG.tag({
				// The `container` parameter can take either the ID of the main element or
				// the main element itself (as either a jQuery or native object)
				container: container,

				// The initial data to load.
				// Different formats might expect different types for `data`:
				// sE.g., the "odin" format expects the annotations as an
				// (already-parsed) Object, while the "brat" format expects them as a raw
				// String.
				// See the full documentation for details.
				data: data,
				format: "odin",

				// Overrides for default options
				options: {
				  showTopMainLabel: true,
                  showTopLinksOnMove: true,
				  showTopArgLabels: false,
				  showBottomMainLabel: true,
                  showBottomLinksOnMove: true,
				  showBottomArgLabels: false,
				  topLinkCategory: category,
				  BottomLinkCategory: category,
				  topTagCategory: "none",
				  bottomTagCategory: "POS",
                  //rowVerticalPadding: 2,
                  compactRows: true,
                  
				}
			});
            basicTag.parser._parsedData.links.forEach((e) => {e.top = true})
            basicTag.redraw()
            if (links.length > 0)
            {
				// find the shift when word amount is changed.
				var shifts = get_shifts(links[0].main.words, basicTag.links[0].main.words);

				var dict = {};
                basicTag.links.forEach((e) => {
                    found = false
                    links.forEach((e2) => {
                        if ((e2.arguments[0].anchor.idx == shifts[e.arguments[0].anchor.idx]) && (((e.trigger in window) && (e2.trigger in window)) || ((!(e.trigger in window)) && (!(e2.trigger in window)) && (e2.trigger.idx == shifts[e.trigger.idx]))))
                        {
                            found = true
                            if (e2.reltype != e.reltype)
                            {
                            	if ((e.reltype.startsWith(e2.reltype)) || ((e.reltype == "compound") && (e2.reltype == "nmod:npmod"))) {
									e.svg.node.style.fill = "#b37700"
									e2.svg.node.style.fill = "#b37700"
								}
                            	else {
                            		found = false
								}
                            }
                        }
                    })

                    if (found == false)
                    {
						var other = -1
						if (!(e.trigger in window))
						{
							other = e.trigger.idx
						}
						var min = Math.min(e.arguments[0].anchor.idx, other)
						var max = Math.max(e.arguments[0].anchor.idx, other)
						pair = [min, max]
						
                        var clash = false
						e.svg.node.style.fill = "#009628"
                        if (pair in dict)
						{
							clash = true
							dict[pair] -= 1
						}
						else
						{
							basicTag.links.every((e3) => {
								if ((e != e3) && ((((shifts[e3.arguments[0].anchor.idx] == shifts[e.arguments[0].anchor.idx]) && (((e.trigger in window) && (e3.trigger in window)) || ((!(e.trigger in window)) && (!(e3.trigger in window)) && (shifts[e3.trigger.idx] == shifts[e.trigger.idx])))) || (((!(e.trigger in window)) && (!(e3.trigger in window)) && (shifts[e3.arguments[0].anchor.idx] == shifts[e.trigger.idx]) && (shifts[e3.trigger.idx] == shifts[e.arguments[0].anchor.idx]))))))
								{
									clash = true
									dict[pair] = -1
									return false;
								}
								return true;
							})
						}
                        if (clash == true)
                        {
                            e.top = false
							e.slot = dict[pair]
                            e.show()
                            basicTag.resize()	
                        }
                    }
                    
                })
                links.forEach((e) => {
                    found = false
                    basicTag.links.forEach((e2) => {
                        if ((shifts[e2.arguments[0].anchor.idx] == e.arguments[0].anchor.idx) && (((e.trigger in window) && (e2.trigger in window)) || ((!(e.trigger in window)) && (!(e2.trigger in window)) && (shifts[e2.trigger.idx] == e.trigger.idx))))
                        {
                            found = true
                        }
                    })

                    if (found == false)
                    {
                        e.svg.node.style.fill = "#FF0000"
                    }
                })
            }
            return basicTag
		}
		
		const version_ret = axios.post('http://34.147.8.119:5000/eud/version/')
		version_ret.then(function(result) {
			version_page = document.getElementById("version")
			version_page.value = result.data.version
		})
		
		const $submitButton = $("#submitButton");
		
		$submitButton.click(async (e) => {
			e.preventDefault();
			var eUd = document.getElementById("GFG1").checked
			var eUdPP = document.getElementById("GFG2").checked
			var eUdBart = document.getElementById("GFG3").checked
			var iterations = document.getElementById("GFG4").value
			var removeEudInfo = document.getElementById("GFG5").checked
			var includeBartInfo = document.getElementById("GFG6").checked
			var limitIterations = document.getElementById("GFG7").checked
			var removeNodeAddingConvs = document.getElementById("GFG8").checked
			var udv = document.getElementById("GFG9").checked

			const $sentenceInput = $("#sentenceInput");
            $sentenceInput[0].value = $sentenceInput[0].value != "" ? $sentenceInput[0].value : "The quick brown fox jumped over the lazy dog."
            
			const response = await axios.post('http://34.147.8.119:5000/eud/annotate/', {sentence: $sentenceInput[0].value, eud: eUd, eud_pp: eUdPP, eud_bart: eUdBart, conv_iterations: limitIterations ? iterations : "inf", remove_eud_info: removeEudInfo, include_bart_info: includeBartInfo, remove_node_adding_convs: removeNodeAddingConvs, udv: udv});

            $('#containerBasic').empty()
            $('#containerPlus').empty()
            
			tag1 = displayTree(response.data.basic, "containerBasic", "universal-basic");
			tag2 = displayTree(response.data.plus, "containerPlus", "universal-enhanced", tag1.links);
			iters = document.getElementById("iters")
			iters.value = response.data.conv_done

			$('html,body').animate({
            	scrollTop: $("#scrollToHere").offset().top
        }, 800);
		});
        
        var slash_idx = window.location.href.lastIndexOf('/')
        if ((slash_idx + 1) != window.location.href.length)
        {
            sliced = window.location.href.slice(slash_idx + 1)
            $("#sentenceInput")[0].value = decodeURIComponent(sliced)
            submitButton.click(this);
        }

        const $showmeButton = $("#showmeButton");

        $showmeButton.click(async (e) => {
			e.preventDefault();
			introJs().start()
		});

        const $feedbackButton = $("#feedbackButton");

        $feedbackButton.click(async (e) => {
			e.preventDefault();
			var feed = window.prompt("Please enter your feedback here:", "You can simply press OK, we will receive the attested senence.")
			if (feed != null)
			{
				var textToSend = ""
				if ((feed != "") && (feed != "You can simply press OK, we will receive the attested senence."))
				{
					textToSend = "User wrote: " + feed + "\n"
				}
				textToSend += "Last sentence input:\n" + $("#sentenceInput")[0].value
				const response = await axios.post('http://34.147.8.119:5000/eud/feedback/', {text_to_send: textToSend});
			}
		});
	}

	return main;
});

function showLimit(checkbox) {
    if (checkbox.checked) {
            document.getElementById("GFG4").style.visibility = "visible"
    } else {
        document.getElementById("GFG4").style.visibility = "hidden"
    }
}

function selectExample(event) {
    var examples = {
		"Possessive modifiers in conjunction": "Bart's father and mother ate donuts.",
		"Genitive Constructions": "Army of zombies. Zombies army.",
		"Aspectual constructions": "Lisa started talking funny.",
		"Copular Sentences": "Sam is the president.",
		"Evidential reconstructions(w/o matrix)": "Sally seems from Britain.",
		"Evidential reconstructions(with matrix)": "Sam seems to fear heights.",
		"Apposition": "E.T., the Extraterrestrial, phones home.",
		"Elaboration/Specification Clauses": "Lisa likes fruits such as apples.",
		"Compounds": "Marge used canola oil.",
		"Passivization Alternation": "The Sheriff was shot by Bob.",
		"Adjectival modifiers": "I see dead people.",
        "Complement control": "Maggie loves talking to friends.",
        "Noun-modifying clauses(reduced relcl)": "The house they made.",
		"Noun-modifying clauses(acl+participle)": "A vision softly creeping, left its seeds.",
		"Noun-modifying clauses(acl+infinitive)": "I designed, the house to build.",
        "Adverbial clauses": "Bart shouldn't text while skating.",
		"Modifiers in conjunction": "Mowgli was taught and raised by wolves.",
		"Hyphen reconstruction": "Homer works at a Seattle-Based company.",
		"Evidential reconstructions(reported)": "The media reported that they achieved peace.",
		"Indexicals": "Sally wonders around in these woods here.",
		"Extended multi-word prepositions": "The child ran ahead of his mother."
	};
    if (event.target.value == "Use loaded examples")
    {
        document.getElementById("sentenceInput").value = ""
        var examplesSelector = document.getElementById("examples");
        examplesSelector.options[0].selected = true;
    }
    else
    {
        document.getElementById("sentenceInput").value = examples[event.target.value]
        document.getElementById("submitButton").click();
    }
}
