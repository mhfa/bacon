import React, { Component } from 'react';
import base64 from 'base-64';

class Base64Form extends Component {

  constructor(){
    super();
    this.state = {
        processedVal: "",
        formVal: "",
    };
  }

  render() {
    const test = 'test';
    const placeholder = `this a ${test}`;
    return (
      <div className="Base64Form">
        <h1>Base64Form</h1>
              <textarea
                rows="4"
                cols="50"
                placeholder={placeholder}
                onChange={this._changeHandlerForm}
                value={this.state.formVal}
              />
              <br />
              <button onClick={this._clickProcessText} id="encode">Encode text to Base 64</button>
              <button onClick={this._clickProcessText} id="decode">Decode Base 64 to text</button>
              <div>
                <h2>Result</h2>
                <p>{this.state.processedVal}</p>
              </div>
      </div>
    );
  }

  _clickProcessText = (e) => {
    let result = "";
    // Debug
    console.log("Form clicked", e.target.id);
    if(e.target.id === "encode") {
      console.log("We are encoding");
      result = base64.encode(this.state.formVal);
    }
    else if(e.target.id === "decode") {
      result = base64.decode(this.state.formVal);
    }
    this.setState({
        processedVal: result,
    });
  }

  _changeHandlerForm = (e) => {
    this.setState({
        formVal: e.target.value,
    });
  }
}

export default Base64Form;
