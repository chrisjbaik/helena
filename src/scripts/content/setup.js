/**********************************************************************
 * Author: S. Chasins
 **********************************************************************/

/**********************************************************************
 * Listeners and general set up
 **********************************************************************/

var tabID = "setme";
utilities.listenForMessage("mainpanel", "content", "likelyRelation", function(msg){RelationFinder.likelyRelation(msg);});
utilities.listenForMessage("background", "content", "tabID", function(msg){tabID = msg; console.log("tab id: ", msg);});
utilities.sendMessage("content", "background", "requestTabID", {});

/**********************************************************************
 * The various node representations we may need
 **********************************************************************/

var NodeRep = (function() { var pub = {};
	pub.nodeToMainpanelNodeRepresentation = function(node){
	  if (node === null){
	    return {text: "", xpath: "", frame: SimpleRecord.getFrameId()};
	  }
	  return {text: NodeRep.nodeToText(node), xpath: nodeToXPath(node), frame: SimpleRecord.getFrameId()};
	}

	pub.nodeToText = function(node){
	  //var text = node.innerText;
	  return getElementText(node);
	}

	function getElementText(el){
	  var text = getElementTextHelper(el);
	  if (text == null || text == undefined || text == ""){ // should empty text also be null?
	    return null;
	  }
	  text = text.trim();
	  return text;
	}

	function getElementTextHelper(el) {
	    var text = '';
	    // Text node (3) or CDATA node (4) - return its text
	    if ( (el.nodeType === 3) || (el.nodeType === 4) ) {
	        return el.nodeValue.trim();
	    // If node is an element (1) and an img, input[type=image], or area element, return its alt text
	    }
	    else if ( (el.nodeType === 1) && (
	            (el.tagName.toLowerCase() == 'img') ||
	            (el.tagName.toLowerCase() == 'area') ||
	            ((el.tagName.toLowerCase() == 'input') && el.getAttribute('type') && (el.getAttribute('type').toLowerCase() == 'image'))
	            ) ) {
	        altText = el.getAttribute('alt')
	        if (altText == null || altText == undefined){
	          altText = ''
	        }
	        return altText.trim();
	        return el.getAttribute('alt').trim() || '';
	    }
	    // Traverse children unless this is a script or style element
	    else if ( (el.nodeType === 1) && !el.tagName.match(/^(script|style)$/i)) {
	        var text = "";
	        var children = el.childNodes;
	        for (var i = 0, l = children.length; i < l; i++) {
	            var newText = getElementText(children[i]);
	            if (newText == null || newText == undefined){
	              newText = "";
	            }
	            if (newText.length > 0){
	              text+=newText+"\n";
	            }
	        }
	        return text;
	    }
	}
return pub;}());