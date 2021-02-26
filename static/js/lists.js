/**
 * @Author: johnhaigh
 * @Date:   2021-01-21T16:27:55+00:00
 * @Last modified by:   johnhaigh
 * @Last modified time: 2021-01-28T09:34:31+00:00
 */

 function add() {
     var num = document.getElementById("t1").rows.length;
     console.log(num);
     var x = document.createElement("tr");

     var a = document.createElement("td");
     var anode = document.createTextNode(num);
     a.appendChild(anode);
     x.appendChild(a);

     a = document.createElement("td");
     anode = document.createElement("input");
     b = document.createAttribute("type");
     b.value = "text";
     anode.setAttribute('name', num);
     anode.setAttributeNode(b);
     a.appendChild(anode);
     x.appendChild(a);

     a = document.createElement("td");
     anode = document.createElement("input");
     b = document.createAttribute("type");
     b.value = "text";
     anode.setAttribute('name', (num + ' owner'));
     anode.setAttributeNode(b);
     a.appendChild(anode);
     x.appendChild(a);

     a = document.createElement("td");
     anode = document.createElement("input");
     b = document.createAttribute("type");
     b.value = "text";
     anode.setAttribute('name', (num + ' notes'));
     anode.setAttributeNode(b);
     a.appendChild(anode);
     x.appendChild(a);

     a = document.createElement("td");
     anode = document.createElement('input');
     anode.setAttribute('class','uk-button uk-button-default');
     anode.setAttribute('type','button');
     anode.setAttribute('value','Delete Row');
   anode.setAttribute('onclick','deleteRow(this)');
     a.appendChild(anode);
     x.appendChild(a);
     document.getElementById("t1").appendChild(x);
 }

 function deleteRow(e,v) {
   var tr = e.parentElement.parentElement;
   var tbl = e.parentElement.parentElement.parentElement;
   tbl.removeChild(tr);

 }
